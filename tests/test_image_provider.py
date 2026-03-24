"""Tests for ImageProvider ABC, ImageRequest/ImageResult dataclasses, and get_provider factory."""

from pathlib import Path

import pytest

from bookforge.images.provider import ImageProvider, ImageRequest, ImageResult
from bookforge.images.providers import get_provider


class TestImageRequest:
    def test_image_request_defaults(self):
        req = ImageRequest(prompt="a cat", reference_images=[Path("ref.png")])
        assert req.prompt == "a cat"
        assert req.reference_images == [Path("ref.png")]
        assert req.width == 1024
        assert req.height == 1024
        assert req.output_format == "png"
        assert req.seed is None
        assert req.model_version is None


class TestImageResult:
    def test_image_result_fields(self):
        result = ImageResult(
            path=Path("out.png"),
            provider="test",
            model_version="v1",
            seed=42,
        )
        assert result.path == Path("out.png")
        assert result.provider == "test"
        assert result.model_version == "v1"
        assert result.seed == 42


class TestImageProviderABC:
    def test_provider_abc_not_instantiable(self):
        with pytest.raises(TypeError):
            ImageProvider()


class TestGetProvider:
    def test_get_provider_flux(self):
        from bookforge.images.providers.flux_kontext import (
            ReplicateFluxKontextProvider,
        )

        provider = get_provider("flux_kontext_pro")
        assert isinstance(provider, ReplicateFluxKontextProvider)

    def test_get_provider_unknown(self):
        with pytest.raises(ValueError, match="Unknown"):
            get_provider("unknown_provider")
