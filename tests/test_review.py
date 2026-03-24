"""Tests for the review logic module."""

from __future__ import annotations

from pathlib import Path

import pytest

from bookforge.story.schema import BilingualText, Book, BookMeta, Page


@pytest.fixture
def sample_book() -> Book:
    """A 2-page book fixture for review testing."""
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
        pages=[
            Page(
                number=1,
                text=BilingualText(
                    en="Hello world this is page one.",
                    ko="안녕하세요 세상 이것은 첫 페이지입니다.",
                ),
                image_prompt="A happy scene",
            ),
            Page(
                number=2,
                text=BilingualText(
                    en="Goodbye world from page two here.",
                    ko="잘가 세상 두번째 페이지에서.",
                ),
                image_prompt="A sad scene",
            ),
        ],
    )


@pytest.fixture
def book_dir_with_assets(tmp_path: Path) -> Path:
    """Book directory with some images and PDFs."""
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    (images_dir / "page-01.png").write_bytes(b"\x89PNG fake")
    (images_dir / "page-02.png").write_bytes(b"\x89PNG fake")
    # Non-matching file should not be counted
    (images_dir / "cover.png").write_bytes(b"\x89PNG fake")

    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "test-book-bilingual-screen.pdf").write_bytes(b"x" * 2048)
    (output_dir / "test-book-bilingual-print.pdf").write_bytes(b"x" * 4096)

    return tmp_path


class TestGatherSummary:
    """Tests for gather_summary function."""

    def test_page_count(self, sample_book: Book, book_dir_with_assets: Path) -> None:
        from bookforge.review import gather_summary

        summary = gather_summary(sample_book, book_dir_with_assets)
        assert summary["page_count"] == 2

    def test_image_count(self, sample_book: Book, book_dir_with_assets: Path) -> None:
        from bookforge.review import gather_summary

        summary = gather_summary(sample_book, book_dir_with_assets)
        assert summary["image_count"] == 2  # Only page-*.png, not cover.png

    def test_word_count_en(self, sample_book: Book, book_dir_with_assets: Path) -> None:
        from bookforge.review import gather_summary

        summary = gather_summary(sample_book, book_dir_with_assets)
        # "Hello world this is page one." = 6 words + "Goodbye world from page two here." = 6 words = 12
        assert summary["word_count_en"] == 12

    def test_word_count_ko(self, sample_book: Book, book_dir_with_assets: Path) -> None:
        from bookforge.review import gather_summary

        summary = gather_summary(sample_book, book_dir_with_assets)
        # Korean words split by whitespace
        # "안녕하세요 세상 이것은 첫 페이지입니다." = 5 + "잘가 세상 두번째 페이지에서." = 4 = 9
        assert summary["word_count_ko"] == 9

    def test_pdf_files(self, sample_book: Book, book_dir_with_assets: Path) -> None:
        from bookforge.review import gather_summary

        summary = gather_summary(sample_book, book_dir_with_assets)
        assert len(summary["pdf_files"]) == 2
        names = {f["name"] for f in summary["pdf_files"]}
        assert "test-book-bilingual-screen.pdf" in names
        assert "test-book-bilingual-print.pdf" in names
        # Check sizes in KB
        for f in summary["pdf_files"]:
            assert "size_kb" in f
            assert f["size_kb"] > 0

    def test_no_images_returns_zero(self, sample_book: Book, tmp_path: Path) -> None:
        from bookforge.review import gather_summary

        summary = gather_summary(sample_book, tmp_path)
        assert summary["image_count"] == 0

    def test_no_pdfs_returns_empty_list(self, sample_book: Book, tmp_path: Path) -> None:
        from bookforge.review import gather_summary

        summary = gather_summary(sample_book, tmp_path)
        assert summary["pdf_files"] == []


class TestReviewChecklist:
    """Tests for REVIEW_CHECKLIST constant."""

    def test_checklist_has_five_items(self) -> None:
        from bookforge.review import REVIEW_CHECKLIST

        assert len(REVIEW_CHECKLIST) == 5

    def test_checklist_items_are_strings(self) -> None:
        from bookforge.review import REVIEW_CHECKLIST

        for item in REVIEW_CHECKLIST:
            assert isinstance(item, str)
            assert len(item) > 0
