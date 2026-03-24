"""ImageProvider ABC and request/result dataclasses for image generation."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ImageRequest:
    """Request parameters for image generation."""

    prompt: str
    reference_images: list[Path]
    output_path: Path = Path("output.png")
    width: int = 1024
    height: int = 1024
    output_format: str = "png"
    seed: int | None = None
    model_version: str | None = None


@dataclass
class ImageResult:
    """Result from image generation."""

    path: Path
    provider: str
    model_version: str
    seed: int | None = None


class ImageProvider(abc.ABC):
    """Abstract base class for image generation providers."""

    @abc.abstractmethod
    async def generate(self, request: ImageRequest) -> ImageResult:
        """Generate an image from the given request."""
        ...

    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        """Return the provider identifier string."""
        ...
