"""Provider factory for image generation."""

from __future__ import annotations

from bookforge.images.provider import ImageProvider


def get_provider(name: str, model_version: str | None = None) -> ImageProvider:
    """Return an ImageProvider instance for the given provider name.

    Raises ValueError for unknown provider names.
    """
    if name == "flux_kontext_pro":
        from bookforge.images.providers.flux_kontext import (
            ReplicateFluxKontextProvider,
        )

        return ReplicateFluxKontextProvider(model_version=model_version)

    raise ValueError(f"Unknown image provider: {name!r}")
