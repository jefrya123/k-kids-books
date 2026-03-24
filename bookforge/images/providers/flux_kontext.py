"""Replicate Flux Kontext Pro image generation provider."""

from __future__ import annotations

import tempfile
from math import gcd
from pathlib import Path

import replicate
from PIL import Image

from bookforge.images.provider import ImageProvider, ImageRequest, ImageResult


# Common aspect ratio mappings supported by Flux Kontext Pro
_ASPECT_RATIOS: dict[tuple[int, int], str] = {
    (1, 1): "1:1",
    (16, 9): "16:9",
    (9, 16): "9:16",
    (4, 3): "4:3",
    (3, 4): "3:4",
    (3, 2): "3:2",
    (2, 3): "2:3",
}


def _aspect_ratio(width: int, height: int) -> str:
    """Derive Flux aspect_ratio string from pixel dimensions."""
    divisor = gcd(width, height)
    reduced = (width // divisor, height // divisor)
    return _ASPECT_RATIOS.get(reduced, "1:1")


def _prepare_reference_image(refs: list[Path]) -> Path | None:
    """Prepare reference image(s) for the API call.

    - 0 refs: return None
    - 1 ref: return the path directly (SDK auto-uploads)
    - 2+ refs: stitch side-by-side into a temp PNG, return that path
    """
    if not refs:
        return None
    if len(refs) == 1:
        return refs[0]

    # Stitch multiple references side-by-side
    images = [Image.open(p) for p in refs]
    max_height = max(img.height for img in images)

    # Resize all to same height, preserving aspect ratio
    resized = []
    for img in images:
        if img.height != max_height:
            scale = max_height / img.height
            new_w = int(img.width * scale)
            img = img.resize((new_w, max_height), Image.LANCZOS)
        resized.append(img)

    total_width = sum(img.width for img in resized)
    stitched = Image.new("RGB", (total_width, max_height))
    x_offset = 0
    for img in resized:
        stitched.paste(img, (x_offset, 0))
        x_offset += img.width

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    stitched.save(tmp.name, format="PNG")
    return Path(tmp.name)


class ReplicateFluxKontextProvider(ImageProvider):
    """Flux Kontext Pro provider via Replicate API."""

    MODEL = "black-forest-labs/flux-kontext-pro"

    def __init__(self, model_version: str | None = None) -> None:
        self._model_version = model_version

    @property
    def provider_name(self) -> str:
        return "replicate/flux-kontext-pro"

    def _model_ref(self) -> str:
        """Return model reference, optionally pinned to a version hash."""
        if self._model_version:
            return f"{self.MODEL}:{self._model_version}"
        return self.MODEL

    async def generate(self, request: ImageRequest) -> ImageResult:
        """Generate an image via Replicate's Flux Kontext Pro model."""
        ref_image = _prepare_reference_image(request.reference_images)

        inputs: dict = {
            "prompt": request.prompt,
            "aspect_ratio": _aspect_ratio(request.width, request.height),
            "output_format": request.output_format,
        }

        if ref_image is not None:
            inputs["input_image"] = ref_image

        if request.seed is not None:
            inputs["seed"] = request.seed

        file_output = await replicate.async_run(
            self._model_ref(), input=inputs
        )

        # Read bytes from FileOutput and write to disk
        image_bytes = await file_output.aread()
        request.output_path.parent.mkdir(parents=True, exist_ok=True)
        request.output_path.write_bytes(image_bytes)

        return ImageResult(
            path=request.output_path,
            provider=self.provider_name,
            model_version=self._model_version or "latest",
            seed=request.seed,
        )
