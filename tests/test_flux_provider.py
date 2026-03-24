"""Tests for ReplicateFluxKontextProvider with stitching and version pinning."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image

from bookforge.images.provider import ImageRequest, ImageResult
from bookforge.images.providers.flux_kontext import ReplicateFluxKontextProvider


@pytest.fixture
def tmp_ref_image(tmp_path: Path) -> Path:
    """Create a small reference PNG for testing."""
    img = Image.new("RGB", (64, 64), color="red")
    p = tmp_path / "ref1.png"
    img.save(p)
    return p


@pytest.fixture
def tmp_ref_images(tmp_path: Path) -> list[Path]:
    """Create two small reference PNGs for multi-ref stitching tests."""
    paths = []
    for i, color in enumerate(["red", "blue"]):
        img = Image.new("RGB", (64, 64), color=color)
        p = tmp_path / f"ref{i}.png"
        img.save(p)
        paths.append(p)
    return paths


@pytest.fixture
def output_path(tmp_path: Path) -> Path:
    return tmp_path / "output.png"


def _make_mock_file_output() -> MagicMock:
    """Create a mock FileOutput with aread() returning fake PNG bytes."""
    # Create a tiny valid PNG in memory
    import io

    buf = io.BytesIO()
    Image.new("RGB", (32, 32), color="green").save(buf, format="PNG")
    png_bytes = buf.getvalue()

    mock_fo = MagicMock()
    mock_fo.aread = AsyncMock(return_value=png_bytes)
    return mock_fo


class TestFluxProviderName:
    def test_flux_provider_name(self):
        provider = ReplicateFluxKontextProvider()
        assert provider.provider_name == "replicate/flux-kontext-pro"


class TestFluxGenerateSingleRef:
    @pytest.mark.asyncio
    async def test_flux_generate_single_ref(
        self, tmp_ref_image: Path, output_path: Path
    ):
        mock_fo = _make_mock_file_output()

        with patch(
            "bookforge.images.providers.flux_kontext.replicate"
        ) as mock_replicate:
            mock_replicate.async_run = AsyncMock(return_value=mock_fo)
            provider = ReplicateFluxKontextProvider()
            request = ImageRequest(
                prompt="a cat",
                reference_images=[tmp_ref_image],
                output_path=output_path,
            )
            result = await provider.generate(request)

        # Verify async_run called with correct args
        call_kwargs = mock_replicate.async_run.call_args
        assert call_kwargs[0][0] == "black-forest-labs/flux-kontext-pro"
        inputs = call_kwargs[1]["input"]
        assert inputs["prompt"] == "a cat"
        assert inputs["aspect_ratio"] == "1:1"
        assert inputs["output_format"] == "png"
        # Single ref: passed directly as Path, no stitching
        assert isinstance(inputs["input_image"], Path)
        assert inputs["input_image"] == tmp_ref_image


class TestFluxGenerateMultiRef:
    @pytest.mark.asyncio
    async def test_flux_generate_multi_ref(
        self, tmp_ref_images: list[Path], output_path: Path
    ):
        mock_fo = _make_mock_file_output()

        with patch(
            "bookforge.images.providers.flux_kontext.replicate"
        ) as mock_replicate:
            mock_replicate.async_run = AsyncMock(return_value=mock_fo)
            provider = ReplicateFluxKontextProvider()
            request = ImageRequest(
                prompt="two characters",
                reference_images=tmp_ref_images,
                output_path=output_path,
            )
            result = await provider.generate(request)

        inputs = mock_replicate.async_run.call_args[1]["input"]
        # Multi ref: stitched into a temp file
        stitched_path = inputs["input_image"]
        assert isinstance(stitched_path, Path)
        assert stitched_path != tmp_ref_images[0]
        assert stitched_path != tmp_ref_images[1]
        # Stitched image should be wider than individual refs
        stitched = Image.open(stitched_path)
        assert stitched.width == 128  # 64 + 64
        assert stitched.height == 64


class TestFluxGenerateNoRef:
    @pytest.mark.asyncio
    async def test_flux_generate_no_ref(self, output_path: Path):
        mock_fo = _make_mock_file_output()

        with patch(
            "bookforge.images.providers.flux_kontext.replicate"
        ) as mock_replicate:
            mock_replicate.async_run = AsyncMock(return_value=mock_fo)
            provider = ReplicateFluxKontextProvider()
            request = ImageRequest(
                prompt="a landscape",
                reference_images=[],
                output_path=output_path,
            )
            result = await provider.generate(request)

        inputs = mock_replicate.async_run.call_args[1]["input"]
        assert "input_image" not in inputs


class TestFluxVersionPinning:
    @pytest.mark.asyncio
    async def test_flux_pinned_version(self, output_path: Path):
        mock_fo = _make_mock_file_output()

        with patch(
            "bookforge.images.providers.flux_kontext.replicate"
        ) as mock_replicate:
            mock_replicate.async_run = AsyncMock(return_value=mock_fo)
            provider = ReplicateFluxKontextProvider(model_version="sha256:abc")
            request = ImageRequest(
                prompt="test",
                reference_images=[],
                output_path=output_path,
            )
            await provider.generate(request)

        model_ref = mock_replicate.async_run.call_args[0][0]
        assert model_ref == "black-forest-labs/flux-kontext-pro:sha256:abc"

    @pytest.mark.asyncio
    async def test_flux_unpinned_version(self, output_path: Path):
        mock_fo = _make_mock_file_output()

        with patch(
            "bookforge.images.providers.flux_kontext.replicate"
        ) as mock_replicate:
            mock_replicate.async_run = AsyncMock(return_value=mock_fo)
            provider = ReplicateFluxKontextProvider()
            request = ImageRequest(
                prompt="test",
                reference_images=[],
                output_path=output_path,
            )
            await provider.generate(request)

        model_ref = mock_replicate.async_run.call_args[0][0]
        assert model_ref == "black-forest-labs/flux-kontext-pro"


class TestFluxReadsOutputBytes:
    @pytest.mark.asyncio
    async def test_flux_reads_output_bytes(self, output_path: Path):
        mock_fo = _make_mock_file_output()

        with patch(
            "bookforge.images.providers.flux_kontext.replicate"
        ) as mock_replicate:
            mock_replicate.async_run = AsyncMock(return_value=mock_fo)
            provider = ReplicateFluxKontextProvider()
            request = ImageRequest(
                prompt="test",
                reference_images=[],
                output_path=output_path,
            )
            result = await provider.generate(request)

        # Verify aread() was called
        mock_fo.aread.assert_awaited_once()
        # Verify output file was written
        assert output_path.exists()
        assert output_path.stat().st_size > 0
        # Verify ImageResult
        assert isinstance(result, ImageResult)
        assert result.path == output_path
        assert result.provider == "replicate/flux-kontext-pro"
