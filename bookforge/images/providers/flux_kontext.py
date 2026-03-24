"""Replicate Flux Kontext Pro image generation provider."""

from __future__ import annotations

from bookforge.images.provider import ImageProvider, ImageRequest, ImageResult


class ReplicateFluxKontextProvider(ImageProvider):
    """Flux Kontext Pro provider via Replicate API."""

    MODEL = "black-forest-labs/flux-kontext-pro"

    def __init__(self, model_version: str | None = None) -> None:
        self._model_version = model_version

    @property
    def provider_name(self) -> str:
        return "replicate/flux-kontext-pro"

    async def generate(self, request: ImageRequest) -> ImageResult:
        raise NotImplementedError("Task 2")
