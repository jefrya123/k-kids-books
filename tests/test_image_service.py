"""Tests for ImageService orchestration: resume, retry, versioning, batch generation."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from replicate.exceptions import ModelError, ReplicateError
from unittest.mock import MagicMock

from bookforge.images.provider import ImageProvider, ImageRequest, ImageResult
from bookforge.images.service import BATCH_SIZE, generate_all, _generate_with_retry
from bookforge.state import load_state, save_state
from bookforge.story.schema import BilingualText, Book, BookMeta, Page
from bookforge.style.schema import (
    ArtStyle,
    CharacterDef,
    ImageConfig,
    Layout,
    StyleGuide,
)


@pytest.fixture
def mock_provider():
    """AsyncMock implementing ImageProvider interface."""
    provider = AsyncMock(spec=ImageProvider)
    provider.provider_name = "mock-provider"

    async def _generate(request: ImageRequest) -> ImageResult:
        # Write a tiny PNG to the output path
        request.output_path.parent.mkdir(parents=True, exist_ok=True)
        request.output_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        return ImageResult(
            path=request.output_path,
            provider="mock-provider",
            model_version="test-v1",
            seed=42,
        )

    provider.generate.side_effect = _generate
    return provider


@pytest.fixture
def sample_book() -> Book:
    """A 3-page sample book for testing."""
    pages = []
    for i in range(1, 4):
        pages.append(
            Page(
                number=i,
                text=BilingualText(en=f"Page {i} text", ko=f"페이지 {i} 텍스트"),
                image_prompt=f"Illustration for page {i}",
            )
        )
    return Book(
        meta=BookMeta(
            title="Test Book",
            title_ko="테스트 책",
            slug="test-book",
            trim_size="8.5x8.5",
            price=4.99,
            ages="4-8",
            style_guide="korean-cute-watercolor",
        ),
        pages=pages,
    )


@pytest.fixture
def sample_style_guide() -> StyleGuide:
    """StyleGuide with 2 characters for testing."""
    return StyleGuide(
        name="korean-cute-watercolor",
        version=1,
        art_style=ArtStyle(
            prompt_prefix="Cute Korean watercolor",
            negative_prompt="photorealistic, dark",
            color_palette=["#FFB5C2"],
        ),
        image=ImageConfig(provider="flux_kontext_pro", width=1024, height=1024),
        characters={
            "ho-rang": CharacterDef(
                name_en="Ho-rang",
                name_ko="호랑",
                description="A friendly tiger cub",
                reference_image="characters/horang-ref.png",
            ),
            "gom-i": CharacterDef(
                name_en="Gom-i",
                name_ko="고미",
                description="A gentle bear cub",
                reference_image="characters/gomi-ref.png",
            ),
        },
    )


@pytest.fixture
def book_dir_with_images(tmp_path: Path) -> Path:
    """Temp book directory with images/ subdir and style-guides sibling."""
    book = tmp_path / "books" / "test-book"
    (book / "images").mkdir(parents=True)
    # Create style-guides sibling with character reference images
    style_dir = tmp_path / "books" / "style-guides" / "characters"
    style_dir.mkdir(parents=True)
    (style_dir / "horang-ref.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)
    (style_dir / "gomi-ref.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)
    return book


class TestGenerateAll:
    """Tests for the generate_all orchestration function."""

    def test_generates_all_pages(
        self, book_dir_with_images, sample_book, sample_style_guide, mock_provider
    ):
        """Service calls provider.generate() for each page. State updated per page."""
        with patch("bookforge.images.service.get_provider", return_value=mock_provider):
            state = asyncio.run(
                generate_all(book_dir_with_images, sample_book, sample_style_guide)
            )

        assert mock_provider.generate.call_count == 3
        for i in range(1, 4):
            page_key = str(i)
            assert page_key in state["pages"]
            assert state["pages"][page_key]["status"] == "ok"
            assert state["pages"][page_key]["image_version"] == 1
            assert "generated_at" in state["pages"][page_key]

    def test_skips_completed_pages(
        self, book_dir_with_images, sample_book, sample_style_guide, mock_provider
    ):
        """Pages with status='ok' in state are skipped."""
        # Pre-populate state: page 1 already done
        pre_state = {
            "pages": {
                "1": {
                    "status": "ok",
                    "image_path": "images/page-01-v1.png",
                    "image_version": 1,
                }
            }
        }
        save_state(book_dir_with_images, pre_state)

        with patch("bookforge.images.service.get_provider", return_value=mock_provider):
            state = asyncio.run(
                generate_all(book_dir_with_images, sample_book, sample_style_guide)
            )

        # Only pages 2 and 3 should be generated
        assert mock_provider.generate.call_count == 2

    def test_redo_specific_pages(
        self, book_dir_with_images, sample_book, sample_style_guide, mock_provider
    ):
        """With redo_pages=[3], only page 3 is regenerated even if status='ok'."""
        pre_state = {
            "pages": {
                "1": {"status": "ok", "image_path": "images/page-01-v1.png", "image_version": 1},
                "2": {"status": "ok", "image_path": "images/page-02-v1.png", "image_version": 1},
                "3": {"status": "ok", "image_path": "images/page-03-v1.png", "image_version": 1},
            }
        }
        save_state(book_dir_with_images, pre_state)

        with patch("bookforge.images.service.get_provider", return_value=mock_provider):
            state = asyncio.run(
                generate_all(
                    book_dir_with_images,
                    sample_book,
                    sample_style_guide,
                    redo_pages=[3],
                )
            )

        # Only page 3 regenerated
        assert mock_provider.generate.call_count == 1

    def test_version_increment(
        self, book_dir_with_images, sample_book, sample_style_guide, mock_provider
    ):
        """Redo generates page-01-v2.png (version 2). Original v1 not deleted."""
        # Create existing v1 file
        v1_path = book_dir_with_images / "images" / "page-01-v1.png"
        v1_path.write_bytes(b"original-v1")

        pre_state = {
            "pages": {
                "1": {"status": "ok", "image_path": "images/page-01-v1.png", "image_version": 1},
                "2": {"status": "ok", "image_path": "images/page-02-v1.png", "image_version": 1},
                "3": {"status": "ok", "image_path": "images/page-03-v1.png", "image_version": 1},
            }
        }
        save_state(book_dir_with_images, pre_state)

        with patch("bookforge.images.service.get_provider", return_value=mock_provider):
            state = asyncio.run(
                generate_all(
                    book_dir_with_images,
                    sample_book,
                    sample_style_guide,
                    redo_pages=[1],
                )
            )

        # v1 still exists
        assert v1_path.exists()
        assert v1_path.read_bytes() == b"original-v1"
        # Version incremented to 2
        assert state["pages"]["1"]["image_version"] == 2
        assert "page-01-v2.png" in state["pages"]["1"]["image_path"]

    def test_retry_transient(
        self, book_dir_with_images, sample_book, sample_style_guide
    ):
        """Provider raises ReplicateError on first 2 attempts, succeeds on 3rd."""
        provider = AsyncMock(spec=ImageProvider)
        provider.provider_name = "mock-provider"

        call_count = 0

        async def _flaky_generate(request: ImageRequest) -> ImageResult:
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ReplicateError("transient failure")
            request.output_path.parent.mkdir(parents=True, exist_ok=True)
            request.output_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
            return ImageResult(
                path=request.output_path,
                provider="mock-provider",
                model_version="test-v1",
                seed=42,
            )

        provider.generate.side_effect = _flaky_generate

        # Use a single-page book for simplicity
        one_page_book = Book(
            meta=sample_book.meta,
            pages=[sample_book.pages[0]],
        )

        with (
            patch("bookforge.images.service.get_provider", return_value=provider),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            state = asyncio.run(
                generate_all(book_dir_with_images, one_page_book, sample_style_guide)
            )

        assert call_count == 3
        assert state["pages"]["1"]["status"] == "ok"

    def test_retry_gives_up(
        self, book_dir_with_images, sample_book, sample_style_guide
    ):
        """Provider raises ReplicateError on all 3 attempts. Page marked failed."""
        provider = AsyncMock(spec=ImageProvider)
        provider.provider_name = "mock-provider"
        provider.generate.side_effect = ReplicateError("persistent failure")

        one_page_book = Book(
            meta=sample_book.meta,
            pages=[sample_book.pages[0]],
        )

        with (
            patch("bookforge.images.service.get_provider", return_value=provider),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            state = asyncio.run(
                generate_all(book_dir_with_images, one_page_book, sample_style_guide)
            )

        assert state["pages"]["1"]["status"] == "failed"
        assert "persistent failure" in state["pages"]["1"]["error"]

    def test_model_error_no_retry(
        self, book_dir_with_images, sample_book, sample_style_guide
    ):
        """ModelError fails immediately with no retry. Provider called exactly once."""
        provider = AsyncMock(spec=ImageProvider)
        provider.provider_name = "mock-provider"
        mock_prediction = MagicMock()
        mock_prediction.error = "bad prompt"
        provider.generate.side_effect = ModelError(mock_prediction)

        one_page_book = Book(
            meta=sample_book.meta,
            pages=[sample_book.pages[0]],
        )

        with (
            patch("bookforge.images.service.get_provider", return_value=provider),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            state = asyncio.run(
                generate_all(book_dir_with_images, one_page_book, sample_style_guide)
            )

        assert provider.generate.call_count == 1
        assert state["pages"]["1"]["status"] == "failed"

    def test_prompt_assembly(
        self, book_dir_with_images, sample_book, sample_style_guide, mock_provider
    ):
        """Request prompt = style_guide.build_prompt_prefix() + '. ' + page.effective_prompt()."""
        one_page_book = Book(
            meta=sample_book.meta,
            pages=[sample_book.pages[0]],
        )

        with patch("bookforge.images.service.get_provider", return_value=mock_provider):
            asyncio.run(
                generate_all(
                    book_dir_with_images, one_page_book, sample_style_guide
                )
            )

        call_args = mock_provider.generate.call_args_list[0]
        request: ImageRequest = call_args[0][0]
        expected_prefix = sample_style_guide.build_prompt_prefix()
        expected_prompt = f"{expected_prefix}. {one_page_book.pages[0].effective_prompt()}"
        assert request.prompt == expected_prompt

    def test_batch_processing(
        self, book_dir_with_images, sample_style_guide, mock_provider
    ):
        """With 7 pages, all pages eventually processed (batched internally)."""
        pages = [
            Page(
                number=i,
                text=BilingualText(en=f"Page {i}", ko=f"페이지 {i}"),
                image_prompt=f"Illustration {i}",
            )
            for i in range(1, 8)
        ]
        big_book = Book(
            meta=BookMeta(
                title="Big Book",
                title_ko="큰 책",
                slug="big-book",
                trim_size="8.5x8.5",
                price=4.99,
                ages="4-8",
                style_guide="korean-cute-watercolor",
            ),
            pages=pages,
        )

        with patch("bookforge.images.service.get_provider", return_value=mock_provider):
            state = asyncio.run(
                generate_all(book_dir_with_images, big_book, sample_style_guide)
            )

        assert mock_provider.generate.call_count == 7
        for i in range(1, 8):
            assert state["pages"][str(i)]["status"] == "ok"

    def test_state_written_after_each_page(
        self, book_dir_with_images, sample_book, sample_style_guide, mock_provider
    ):
        """After each page generation, save_state is called (atomic per page)."""
        with (
            patch("bookforge.images.service.get_provider", return_value=mock_provider),
            patch("bookforge.images.service.save_state") as mock_save,
        ):
            asyncio.run(
                generate_all(book_dir_with_images, sample_book, sample_style_guide)
            )

        # save_state called once per page (3 pages)
        assert mock_save.call_count == 3


class TestGenerateWithRetry:
    """Tests for the retry logic."""

    def test_retry_on_timeout(self):
        """httpx.TimeoutException also triggers retry."""
        provider = AsyncMock(spec=ImageProvider)
        call_count = 0

        async def _timeout_then_ok(request):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise httpx.TimeoutException("timeout")
            return ImageResult(
                path=Path("test.png"),
                provider="mock",
                model_version="v1",
            )

        provider.generate.side_effect = _timeout_then_ok

        request = ImageRequest(prompt="test", reference_images=[])

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = asyncio.run(_generate_with_retry(provider, request))

        assert call_count == 2
        assert result.provider == "mock"
