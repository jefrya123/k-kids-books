"""Image generation orchestration: resume, retry, versioning, batch processing."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

import httpx
from replicate.exceptions import ModelError, ReplicateError

from bookforge.images.provider import ImageRequest, ImageResult
from bookforge.images.providers import get_provider
from bookforge.state import load_state, save_state
from bookforge.story.schema import Book, Page
from bookforge.style.schema import StyleGuide

BATCH_SIZE = 3


async def generate_all(
    book_dir: Path,
    book: Book,
    style_guide: StyleGuide,
    redo_pages: list[int] | None = None,
) -> dict:
    """Orchestrate page-by-page image generation with resume, retry, and versioning.

    Returns the final state dict after processing all pages.
    """
    state = load_state(book_dir)
    if "pages" not in state:
        state["pages"] = {}

    provider = get_provider(
        style_guide.image.provider, state.get("model_version")
    )

    # Resolve character reference image paths
    ref_images = [
        book_dir.parent / "style-guides" / c.reference_image
        for c in style_guide.characters.values()
    ]

    prompt_prefix = style_guide.build_prompt_prefix()

    # Select pages to process
    pages_to_run: list[Page] = []
    for page in book.pages:
        page_key = str(page.number)
        page_state = state["pages"].get(page_key, {})

        if redo_pages and page.number in redo_pages:
            pages_to_run.append(page)
        elif page_state.get("status") == "ok":
            continue  # Skip completed pages
        else:
            pages_to_run.append(page)

    # Process in batches
    for i in range(0, len(pages_to_run), BATCH_SIZE):
        batch = pages_to_run[i : i + BATCH_SIZE]
        tasks = [
            _generate_page(
                book_dir, page, prompt_prefix, ref_images, provider, state
            )
            for page in batch
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    return state


async def _generate_page(
    book_dir: Path,
    page: Page,
    prompt_prefix: str,
    ref_images: list[Path],
    provider,
    state: dict,
) -> None:
    """Generate a single page image with retry and versioning."""
    page_key = str(page.number)
    page_state = state["pages"].get(page_key, {})

    # Determine next version
    current_version = page_state.get("image_version", 0)
    next_version = current_version + 1

    # Build output path
    output_path = (
        book_dir / "images" / f"page-{page.number:02d}-v{next_version}.png"
    )

    # Assemble prompt
    prompt = f"{prompt_prefix}. {page.effective_prompt()}"

    request = ImageRequest(
        prompt=prompt,
        reference_images=ref_images,
        output_path=output_path,
        width=1024,
        height=1024,
        model_version=state.get("model_version"),
    )

    try:
        result = await _generate_with_retry(provider, request)
        state["pages"][page_key] = {
            "status": "ok",
            "image_path": f"images/page-{page.number:02d}-v{next_version}.png",
            "image_version": next_version,
            "seed": result.seed,
            "model_version": result.model_version,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        state["pages"][page_key] = {
            **page_state,
            "status": "failed",
            "error": str(exc),
            "image_version": current_version or 1,
        }

    save_state(book_dir, state)


async def _generate_with_retry(
    provider, request: ImageRequest, max_attempts: int = 3
) -> ImageResult:
    """Retry on transient errors with exponential backoff. ModelError fails immediately."""
    for attempt in range(max_attempts):
        try:
            return await provider.generate(request)
        except ModelError:
            raise  # No retry for model/prompt errors
        except (ReplicateError, httpx.TimeoutException):
            if attempt == max_attempts - 1:
                raise
            await asyncio.sleep(2**attempt)
    # Should never reach here, but satisfy type checker
    raise RuntimeError("Exhausted retry attempts")  # pragma: no cover
