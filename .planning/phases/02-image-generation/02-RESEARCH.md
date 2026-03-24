# Phase 2: Image Generation — Research

**Researched:** 2026-03-24
**Domain:** Replicate SDK 1.0.7, Flux Kontext Pro, async image generation, provider abstraction
**Confidence:** HIGH (SDK verified from installed source; API surface confirmed; Flux input schema MEDIUM from WebSearch cross-ref)

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CLI-02 | `uv run bookforge illustrate <slug>` generates images for all pages | Typer command pattern from Phase 1; `ImageService.run_all()` driven by CLI |
| IMG-01 | Flux Kontext Pro via Replicate as default provider with character reference images | `replicate.async_run("black-forest-labs/flux-kontext-pro", input={...})` — input_image accepts open file handle; local Path auto-uploaded via SDK |
| IMG-02 | Abstract image provider interface, swappable via config change | `ImageProvider` ABC; factory via `style_guide.yaml` `image.provider` field |
| IMG-03 | One illustration per page plus cover (~10-12 per book) | `ImageService` iterates `Book.pages`; cover is page 0 |
| IMG-04 | `--redo N,N` flag to regenerate specific pages without regenerating all | Typer option `--redo`; comma-split page numbers; `ImageService.run_pages(nums)` |
| IMG-05 | Image versioning — regenerated images saved alongside originals | `page-03-v1.png`, `page-03-v2.png`; state tracks current version per page |
| IMG-06 | HTML contact sheet generated after illustration for quick visual review | Jinja2 template + Pillow thumbnails; write to `images/contact-sheet.html` |
| IMG-07 | Skip already-generated images on re-run (resume support) | State `pages[N].status == "ok"` check before API call |
| IMG-08 | Retry transient API failures up to 3 times with exponential backoff | `ReplicateError` (status 429/5xx) + `ModelError` — manual retry loop; SDK does NOT auto-retry |
| IMG-09 | Pin Replicate model version hash for reproducibility | Pass `"black-forest-labs/flux-kontext-pro:<sha>"` to `replicate.async_run()`; store hash in `style_guide.yaml` |

</phase_requirements>

---

## Summary

Phase 2 wires the Replicate Python SDK 1.0.7 to generate one illustration per book page using Flux Kontext Pro, with character consistency enforced through reference images, async concurrency for speed, and a robust resume/retry/versioning system.

The SDK is already confirmed installed (1.0.7, verified from source). The key architectural insight from reading the SDK source directly: `replicate.async_run()` accepts a `Path` object for any file input — the SDK automatically uploads it to Replicate's file storage and substitutes a URL. This means reference images are passed as `input_image=Path("style-guides/characters/horang-ref.png")` — no manual upload step needed. Output is a `FileOutput` object (not a raw URL) with `.read()` / `.aread()` methods that download the image bytes.

The Flux Kontext Pro model takes a **single** `input_image` for character reference. For multi-character pages, the architecture research and official Black Forest Labs guidance is to stitch both character reference images side-by-side into a single combined PNG before passing it. The input_image is the "style/character anchor" and the prompt drives the scene composition.

**Primary recommendation:** Use `replicate.async_run()` with `asyncio.gather()` for concurrent generation of all pages in batches of 3-4. Pages are sequential enough that small batches (not all-at-once) catch prompt errors early before wasting money.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| replicate | 1.0.7 | Replicate API client | Already installed; 1.0.x stable API; async_run + FileOutput confirmed from SDK source |
| Pillow | 12.1.1 | Image validation, thumbnail generation for contact sheet | Already added to pyproject.toml; verify dimensions, generate contact sheet thumbnails |
| httpx | 0.28.1 | Internal to Replicate SDK; also available for direct use | Already a transitive dep; available for any future provider that needs direct HTTP |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| asyncio (stdlib) | N/A | Concurrent page generation via `asyncio.gather()` | Always — async_run is the primary generation path |
| pytest-asyncio | current | Test async provider code | Already in dev deps; needed for testing `async def generate()` |
| respx | current | Mock httpx calls to Replicate in tests | Already in dev deps; mock `POST /v1/predictions` and `GET /v1/files` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Flux Kontext Pro | Flux Kontext Max | Max is higher quality but costs ~2-3x more; reserve as `--quality max` flag for cover |
| replicate.async_run() | Direct HTTP via httpx | async_run handles file upload, polling, FileOutput wrapping — no reason to drop down |
| Manual retry loop | tenacity library | tenacity adds a dependency; a 3-attempt manual loop is 8 lines and has no transitive deps |

**Installation (already added):**
```bash
uv add replicate pillow httpx
```

---

## Architecture Patterns

### Recommended Project Structure

```
bookforge/
  images/
    __init__.py
    service.py          # ImageService — orchestration, resume, retry, versioning
    provider.py         # ImageProvider ABC + ImageRequest/ImageResult dataclasses
    contact_sheet.py    # HTML contact sheet generator
    providers/
      __init__.py       # get_provider() factory
      flux_kontext.py   # ReplicateFluxKontextProvider
  cli/
    illustrate.py       # CLI command: bookforge illustrate <slug>
```

### Pattern 1: Provider ABC + Factory

**What:** Abstract base class for image generation. `ImageProvider` protocol with `async generate(request) -> ImageResult`. Factory reads provider name from `StyleGuide.image.provider`.

**When to use:** Always. Required for IMG-02.

```python
# bookforge/images/provider.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ImageRequest:
    prompt: str                        # full assembled prompt (style + chars + page)
    reference_images: list[Path]       # character reference image paths
    width: int = 1024
    height: int = 1024
    output_format: str = "png"
    seed: int | None = None
    model_version: str | None = None   # pinned SHA or None for latest


@dataclass
class ImageResult:
    path: Path                         # saved local file path
    provider: str
    model_version: str
    seed: int | None = None


class ImageProvider(ABC):
    @abstractmethod
    async def generate(self, request: ImageRequest) -> ImageResult: ...

    @property
    @abstractmethod
    def provider_name(self) -> str: ...
```

### Pattern 2: Flux Kontext Pro Provider

**What:** Concrete Replicate implementation. Opens reference image as file handle (SDK auto-uploads). Output is `FileOutput` — call `.aread()` to get bytes, then write to disk.

**Key insight from SDK source (helpers.py line 41-43):** When a `Path` is passed as an input value, `encode_json` opens it as `rb` and calls `client.files.create()` to upload it, substituting the upload URL. This happens transparently in `async_run()`.

```python
# bookforge/images/providers/flux_kontext.py
import asyncio
import replicate
from pathlib import Path
from bookforge.images.provider import ImageProvider, ImageRequest, ImageResult


class ReplicateFluxKontextProvider(ImageProvider):
    # Source: confirmed from replicate SDK source + WebSearch on flux-kontext-pro API
    MODEL = "black-forest-labs/flux-kontext-pro"

    def __init__(self, model_version: str | None = None) -> None:
        # model_version: None uses latest; set to SHA for IMG-09 pinning
        self._model_version = model_version

    @property
    def provider_name(self) -> str:
        return "replicate/flux-kontext-pro"

    def _model_ref(self) -> str:
        if self._model_version:
            return f"{self.MODEL}:{self._model_version}"
        return self.MODEL

    async def generate(self, request: ImageRequest) -> ImageResult:
        # Stitch multi-character references into single image before passing
        ref_image = _prepare_reference_image(request.reference_images)

        inputs: dict = {
            "prompt": request.prompt,
            "aspect_ratio": _aspect_ratio(request.width, request.height),
            "output_format": request.output_format,
        }
        if ref_image:
            inputs["input_image"] = ref_image  # Path — SDK uploads automatically
        if request.seed is not None:
            inputs["seed"] = request.seed

        output = await replicate.async_run(self._model_ref(), input=inputs)
        # output is FileOutput (or list of FileOutput for some models)
        file_output = output[0] if isinstance(output, list) else output
        return file_output  # caller saves bytes via .aread()
```

### Pattern 3: ImageService — Orchestration, Resume, Retry, Versioning

**What:** Top-level service that iterates pages, checks state, calls provider, retries on failure, saves versioned output, updates state atomically.

**When to use:** Always. The CLI delegates entirely to this.

```python
# bookforge/images/service.py (structural sketch)
async def generate_all(
    book_dir: Path,
    book: Book,
    style_guide: StyleGuide,
    redo_pages: list[int] | None = None,
) -> None:
    state = load_state(book_dir)
    provider = get_provider(style_guide)

    pages_to_run = _select_pages(book.pages, state, redo_pages)

    # Process in batches of BATCH_SIZE (3-4) to catch errors early
    for batch in _batches(pages_to_run, size=3):
        tasks = [_generate_page(book_dir, page, style_guide, provider, state)
                 for page in batch]
        await asyncio.gather(*tasks, return_exceptions=True)
        # Check results: surface failures before continuing
```

### Pattern 4: Retry Logic

**What:** Manual 3-attempt exponential backoff. Retry on `ReplicateError` (HTTP 429/5xx) and `httpx.TimeoutException`. Do NOT retry on `ModelError` (user prompt error — permanent failure).

**When to use:** Wraps every `provider.generate()` call.

```python
# Source: replicate SDK exceptions.py — ReplicateError has .status field
import asyncio
import httpx
from replicate.exceptions import ModelError, ReplicateError

async def _generate_with_retry(provider, request, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return await provider.generate(request)
        except ModelError:
            raise  # permanent — bad prompt, content policy, etc.
        except (ReplicateError, httpx.TimeoutException) as exc:
            if attempt == max_attempts - 1:
                raise
            wait = 2 ** attempt  # 1s, 2s, 4s
            await asyncio.sleep(wait)
```

### Pattern 5: Image Versioning

**What:** Before saving a new image for page N, check state for existing version. Increment version suffix. Never overwrite.

```python
def _next_version_path(book_dir: Path, page_num: int) -> Path:
    images_dir = book_dir / "images"
    v = 1
    while True:
        candidate = images_dir / f"page-{page_num:02d}-v{v}.png"
        if not candidate.exists():
            return candidate
        v += 1
```

### Pattern 6: HTML Contact Sheet

**What:** After all pages complete, render a single HTML file showing all page thumbnails in a grid. Uses Pillow to generate 200px thumbnails, Jinja2 (already installed) for the HTML template.

```python
# bookforge/images/contact_sheet.py
# Generate thumbnail for each page image via Pillow Image.thumbnail()
# Render grid HTML with Jinja2 template
# Write to book_dir / "images" / "contact-sheet.html"
```

### Pattern 7: Multi-Character Reference Stitching

**What:** When both Ho-rang and Gom-i need to appear, stitch their reference PNGs side-by-side into a temp file using Pillow before passing to the API.

**Why:** Official Black Forest Labs recommendation; confirmed in PITFALLS.md Pitfall 2.

```python
# bookforge/images/providers/flux_kontext.py
from PIL import Image
import tempfile

def _prepare_reference_image(refs: list[Path]) -> Path | None:
    if not refs:
        return None
    if len(refs) == 1:
        return refs[0]
    # Stitch side-by-side
    images = [Image.open(r) for r in refs]
    height = max(img.height for img in images)
    total_width = sum(img.width for img in images)
    combined = Image.new("RGB", (total_width, height))
    x = 0
    for img in images:
        combined.paste(img, (x, 0))
        x += img.width
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    combined.save(tmp.name)
    return Path(tmp.name)
```

### Pattern 8: CLI Command

**What:** `bookforge illustrate <slug>` with optional `--redo` flag.

```python
# bookforge/cli/illustrate.py
import asyncio
import typer
from pathlib import Path

def illustrate(
    slug: str = typer.Argument(..., help="Book slug"),
    redo: str | None = typer.Option(
        None, "--redo",
        help="Comma-separated page numbers to regenerate, e.g. '3,7' or 'all'"
    ),
) -> None:
    # Parse redo_pages from redo string
    # Load book + style guide
    # asyncio.run(image_service.generate_all(...))
    # Show Rich progress
```

### Anti-Patterns to Avoid

- **Passing `input_image` as a URL string for local files:** Pass a `Path` object — the SDK uploads it and handles the URL substitution. Constructing a file:// URL or pre-uploading manually is unnecessary.
- **Using `replicate.run()` (synchronous) for all pages sequentially:** This blocks between every prediction. Use `async_run()` + `asyncio.gather()` for batch concurrency.
- **Checking `prediction.output` as a string URL:** The SDK's `transform_output()` wraps URLs into `FileOutput` objects. Call `.read()` or `.aread()` on the result — do not treat it as a string.
- **Catching only `ReplicateError` for retries:** Also catch `httpx.TimeoutException` — cold starts can time out the HTTP request even before the prediction fails.
- **Generating all 12 images before checking any:** Use batches of 3-4. A bad prompt on page 1 will fail 11 other calls if all submitted at once.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| File upload to Replicate | Custom upload + URL management | `Path` as input value to `async_run()` | SDK's `encode_json()` handles upload automatically (confirmed from helpers.py source) |
| HTTP retries with backoff | Custom sleep loop | `asyncio.sleep(2**attempt)` in 3-attempt loop | Simple enough; tenacity adds a dep for no gain at this scale |
| Image resize/validate | Custom pixel math | `Pillow Image.open()` + `.verify()` + `.size` | Pillow already in stack; handles all image format edge cases |
| Image stitching | Custom raw byte manipulation | `Pillow Image.new()` + `.paste()` | Pillow's compose API is 6 lines; no reason to hand-roll |
| Contact sheet HTML | Custom string concatenation | Jinja2 (already installed) | Consistent with project's HTML templating approach |

**Key insight:** The Replicate SDK handles the hard parts of file I/O, polling, and output wrapping. The provider implementation is thin orchestration, not infrastructure.

---

## Common Pitfalls

### Pitfall 1: Output is FileOutput, Not a URL String
**What goes wrong:** Code tries to use `str(output)` as a file path, or passes output directly to `Path()` constructor.
**Why it happens:** The pre-1.0 SDK returned URL strings directly. The current SDK returns `FileOutput` objects.
**How to avoid:** Always call `await output.aread()` to get bytes, then write to disk manually.
**Warning signs:** `AttributeError: 'FileOutput' object has no attribute...` or saving a file that contains a URL string instead of image bytes.

### Pitfall 2: Single input_image vs Multiple Reference Images
**What goes wrong:** Flux Kontext Pro accepts exactly ONE `input_image`. Passing a list raises a validation error.
**Why it happens:** The architecture assumes multiple reference images; the API accepts only one.
**How to avoid:** Use `_prepare_reference_image()` to stitch multiple refs into a single PNG before any API call. For single-character pages, pass the one ref directly.
**Warning signs:** Replicate `ModelError` with an input validation message.

### Pitfall 3: Model Version Hash Not Pinnable via Model Name Alone
**What goes wrong:** `black-forest-labs/flux-kontext-pro` always runs the latest deployed version. Regenerating a page months later may produce subtly different style due to model updates.
**Why it happens:** The model identifier without a version hash is mutable (Replicate rolls forward).
**How to avoid:** Store the version hash from the first successful prediction (`prediction.version` field on the `Prediction` object) in `state.json` and in `style_guide.yaml`. On subsequent runs, use `black-forest-labs/flux-kontext-pro:<hash>`.
**Warning signs:** Visual style drift between pages generated in different sessions.

### Pitfall 4: Cold Start Timeout on First Prediction
**What goes wrong:** The first call to `async_run()` hangs with no output for 20-45 seconds. Users Ctrl+C, assuming a crash.
**Why it happens:** Replicate boots the model container on demand. Default poll interval is 0.5s (confirmed from client.py line 61). The container startup is counted in that polling window.
**How to avoid:** Show a Rich status spinner with elapsed time immediately on CLI entry. Write `page.status = "starting"` to state before the API call so Ctrl+C leaves a recoverable state.
**Warning signs:** No output for >15s on first run after model has been idle.

### Pitfall 5: Image Resolution Insufficient for Print
**What goes wrong:** Flux Kontext Pro default output may not reach 2625px minimum for 8.75" × 8.75" at 300 DPI.
**Why it happens:** The `aspect_ratio` parameter controls proportions, not absolute pixel dimensions. Actual resolution depends on the model's internal render size.
**How to avoid:** After saving each image, validate pixel dimensions with Pillow: `img.size` must meet `(trim_w + 2*bleed) * dpi` minimum. Flag undersized images in state and in CLI output.
**Warning signs:** `Image.open(path).size` returns `(1024, 1024)` when you need `(2625, 2625)`.

### Pitfall 6: State File Written After Image Download — Partial Failure
**What goes wrong:** Image is generated and downloaded, but process crashes before state is updated. Next run re-generates the same image (wastes money) or produces a v2 when v1 is still good.
**Why it happens:** State write happens after image write — a crash between them leaves state inconsistent.
**How to avoid:** Use the atomic `save_state()` (already implemented in `state.py`) immediately after writing the image file. The image filename is the ground truth; state is the index.

---

## Code Examples

Verified from installed SDK source (replicate 1.0.7):

### Basic Async Run with File Input

```python
# Source: replicate/helpers.py lines 41-43 — Path -> auto-upload via files.create()
import replicate
from pathlib import Path

output = await replicate.async_run(
    "black-forest-labs/flux-kontext-pro",
    input={
        "prompt": "Ho-rang the tiger cub waves hello on a sunny hillside",
        "input_image": Path("style-guides/characters/horang-ref.png"),  # auto-uploaded
        "aspect_ratio": "1:1",
        "output_format": "png",
        "seed": 42,
    }
)
# output is FileOutput (replicate/helpers.py lines 118-192)
image_bytes = await output.aread()  # download image bytes
Path("books/mybook/images/page-01-v1.png").write_bytes(image_bytes)
```

### Pinned Version Hash Usage

```python
# Source: replicate/run.py lines 44-48 — version_id path in run()
# Get hash from first prediction:
#   prediction.version -> "abc123..."
# Pin in style_guide.yaml: image.model_version: "abc123..."

model_ref = f"black-forest-labs/flux-kontext-pro:{model_version_hash}"
output = await replicate.async_run(model_ref, input=inputs)
```

### Concurrent Batch Generation

```python
# Source: replicate/run.py async_run() confirmed; asyncio.gather() stdlib
import asyncio

async def generate_batch(pages: list[Page], ...) -> None:
    tasks = [generate_page(page, ...) for page in pages]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for page, result in zip(pages, results):
        if isinstance(result, Exception):
            # log failure, update state, continue
            ...
```

### Catching the Right Exceptions

```python
# Source: replicate/exceptions.py — ModelError vs ReplicateError
from replicate.exceptions import ModelError, ReplicateError
import httpx

async def generate_with_retry(provider, request, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return await provider.generate(request)
        except ModelError:
            raise  # bad prompt or content policy — don't retry
        except (ReplicateError, httpx.TimeoutException) as exc:
            if attempt == max_attempts - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # 1s, 2s, 4s
```

### Validate Image Dimensions Post-Download

```python
# Source: Pillow Image.open() — standard pattern
from PIL import Image
import io

def validate_image_size(image_bytes: bytes, min_px: int = 2625) -> bool:
    img = Image.open(io.BytesIO(image_bytes))
    w, h = img.size
    return w >= min_px and h >= min_px
```

### HTML Contact Sheet (structural)

```python
# bookforge/images/contact_sheet.py
from PIL import Image
import io
import base64
from pathlib import Path

def generate_contact_sheet(book_dir: Path, page_paths: list[Path]) -> Path:
    thumbnails = []
    for p in page_paths:
        img = Image.open(p)
        img.thumbnail((200, 200))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        thumbnails.append({"name": p.name, "data": b64})
    # render Jinja2 template with thumbnails list
    # write to book_dir / "images" / "contact-sheet.html"
    ...
```

---

## Flux Kontext Pro — Input Parameters

Confirmed from WebSearch cross-referencing Replicate model page, fal.ai docs, and official BFL documentation:

| Parameter | Type | Notes |
|-----------|------|-------|
| `prompt` | str | Required. The editing/generation instruction. |
| `input_image` | file / URL | Optional. Single reference image for character/style consistency. Pass a `Path` object; SDK uploads automatically. |
| `aspect_ratio` | str | One of: `1:1`, `16:9`, `9:16`, `4:3`, `3:4`, `3:2`, `2:3`, `4:5`, `5:4`, `21:9`, `9:21`, `2:1`, `1:2`. Use `1:1` for square book pages. |
| `output_format` | str | `"png"` or `"jpeg"`. Use `"png"` for print quality. |
| `seed` | int | Optional. Fixes randomness for reproducibility. Store seed in state. |
| `safety_tolerance` | int | 0 (strictest) to 6 (permissive). Default appropriate for children's books. |
| `guidance` | float | Prompt adherence strength. Leave at default unless output deviates from prompt. |

**Output:** `FileOutput` object. Call `.aread()` (async) or `.read()` (sync) to get PNG/JPEG bytes.

**Confidence:** MEDIUM — parameters sourced from WebSearch against Replicate/fal.ai/BFL docs, not directly verified via live API call. The `input_image`, `prompt`, `aspect_ratio`, `output_format`, and `seed` parameters are high-confidence (multi-source agreement). `safety_tolerance` and `guidance` are MEDIUM (single source).

---

## Pricing

**Flux Kontext Pro cost:** ~$0.04 per image (confirmed via multiple sources: fal.ai lists $0.04/image; BFL credits pricing 4 credits = $0.04; MindStudio documentation).

**Budget check:**
- 12 pages + 1 cover = 13 images per book
- At $0.04/image: $0.52 per book run
- With 3x retries budget: ~$1.56 worst case
- Well within the $15 target budget per book
- Reserve `flux-kontext-max` (estimated $0.08-0.16/image) for cover art only

**Confidence:** MEDIUM — $0.04 confirmed via fal.ai pricing page and BFL credits page. Replicate may differ slightly (compute-time pricing). Actual Replicate price not directly confirmed from replicate.com (WebFetch blocked). Treat $0.04 as a floor estimate; Replicate may charge $0.05-0.08.

---

## Model Version Pinning

**How to pin (confirmed from SDK source):**

The `Prediction` object (prediction.py line 55-56) has a `version` field that contains the exact version hash used for a prediction. After the first successful generation run:

1. Inspect `prediction.version` from the raw prediction object (not exposed by `async_run()` directly — need `predictions.create()` path to access it).
2. Store the hash in `style_guide.yaml` as `image.model_version: "sha256:abc123..."`.
3. Construct model ref as `f"black-forest-labs/flux-kontext-pro:{hash}"`.

**Alternative:** Use `client.models.versions.list("black-forest-labs/flux-kontext-pro")` to enumerate available version hashes before the first run, then pin to the current one.

**Important:** To capture the version hash from an `async_run()` call, use the lower-level `predictions.async_create()` path instead, which returns a `Prediction` object with `.version` field. Store `prediction.version` in `state.json["model_version"]` on the first run.

---

## State Schema Extension for Phase 2

The existing `state.json` schema (from ARCHITECTURE.md) needs these additions:

```json
{
  "version": 1,
  "slug": "dangun-story",
  "model_version": "sha256:abc123...",
  "stages": {
    "illustrate": "complete"
  },
  "pages": {
    "01": {
      "status": "ok",
      "image_path": "images/page-01-v1.png",
      "image_version": 1,
      "seed": 42,
      "model_version": "sha256:abc123...",
      "generated_at": "2026-03-24T10:00:00Z"
    },
    "02": {
      "status": "failed",
      "error": "ModelError: content policy",
      "image_path": null,
      "image_version": 0,
      "seed": null,
      "model_version": null
    }
  }
}
```

New fields: `image_version` (int, for versioned filenames), `seed`, `model_version` per page, `generated_at`. Top-level `model_version` is the session default.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (stdlib) + pytest-asyncio |
| Config file | `pyproject.toml` — `[tool.pytest.ini_options]` `testpaths = ["tests"]` |
| Quick run command | `uv run pytest tests/test_image_provider.py tests/test_image_service.py -x` |
| Full suite command | `uv run pytest tests/ -x` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| IMG-01 | Provider calls Replicate with correct input_image + prompt | unit | `uv run pytest tests/test_image_provider.py::test_flux_generate -x` | Wave 0 |
| IMG-02 | get_provider() returns correct class from style guide | unit | `uv run pytest tests/test_image_provider.py::test_get_provider_factory -x` | Wave 0 |
| IMG-03 | Service iterates all pages + cover | unit | `uv run pytest tests/test_image_service.py::test_generates_all_pages -x` | Wave 0 |
| IMG-04 | --redo skips non-specified pages | unit | `uv run pytest tests/test_image_service.py::test_redo_specific_pages -x` | Wave 0 |
| IMG-05 | v2 file saved alongside v1, v1 not overwritten | unit | `uv run pytest tests/test_image_service.py::test_version_increment -x` | Wave 0 |
| IMG-06 | Contact sheet HTML written with correct image refs | unit | `uv run pytest tests/test_contact_sheet.py::test_contact_sheet_written -x` | Wave 0 |
| IMG-07 | State ok pages skipped (no API call) | unit | `uv run pytest tests/test_image_service.py::test_skips_completed_pages -x` | Wave 0 |
| IMG-08 | Retries 3x on ReplicateError, raises on ModelError | unit | `uv run pytest tests/test_image_service.py::test_retry_transient -x` | Wave 0 |
| IMG-09 | Model ref includes version hash when set in style guide | unit | `uv run pytest tests/test_image_provider.py::test_pinned_version_hash -x` | Wave 0 |
| CLI-02 | CLI command invokes service with correct slug + redo | unit | `uv run pytest tests/test_illustrate_cli.py -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/test_image_provider.py tests/test_image_service.py -x`
- **Per wave merge:** `uv run pytest tests/ -x`
- **Phase gate:** Full suite green before marking phase complete

### Wave 0 Gaps

- [ ] `tests/test_image_provider.py` — covers IMG-01, IMG-02, IMG-09
- [ ] `tests/test_image_service.py` — covers IMG-03, IMG-04, IMG-05, IMG-07, IMG-08
- [ ] `tests/test_contact_sheet.py` — covers IMG-06
- [ ] `tests/test_illustrate_cli.py` — covers CLI-02
- [ ] `tests/conftest.py` additions — mock FileOutput, mock Prediction object, sample book with 2 pages

---

## Open Questions

1. **Actual Replicate pricing for flux-kontext-pro**
   - What we know: fal.ai charges $0.04/image; BFL direct API is $0.04/image via credits
   - What's unclear: Replicate's specific compute-second pricing for this model
   - Recommendation: Run one test prediction and check the Replicate billing dashboard before treating $0.04 as confirmed. Budget $0.10/image as safe upper bound for planning.

2. **Version hash retrieval from async_run()**
   - What we know: `async_run()` returns output only, not the Prediction object; `Prediction.version` field exists in SDK
   - What's unclear: Whether `async_run()` with `use_file_output=True` exposes the prediction metadata post-run
   - Recommendation: Use `client.predictions.async_create(model=..., input=...)` path for the first run to capture the version hash, then switch to `async_run()` for subsequent calls with the pinned hash. Log this as a Wave 1 decision.

3. **Flux Kontext Pro output resolution**
   - What we know: Model outputs vary by aspect_ratio; exact pixel dimensions not confirmed
   - What's unclear: Whether 1:1 aspect ratio produces 1024x1024 (insufficient for print) or higher
   - Recommendation: The post-download Pillow validation step (validate_image_size) is mandatory — it will catch undersized images immediately. If output is 1024x1024, add an upscale step (e.g., Replicate `nightmareai/real-esrgan` upscaler) as a post-processing task. Flag this as a Wave 1 spike.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| SDK returns URL strings | SDK returns `FileOutput` objects | replicate SDK 1.0.x | Must call `.read()` / `.aread()` — not a string |
| Separate file upload step | Pass `Path` directly as input | replicate SDK 0.x → 1.0 | SDK auto-uploads; no pre-upload needed |
| `replicate.run()` synchronous only | `replicate.async_run()` available | replicate 0.8+ | Concurrent page generation is now native |
| Polling interval hardcoded | `REPLICATE_POLL_INTERVAL` env var | replicate 1.0.x | Can be tuned for tests (set to 0.01) |

**Deprecated/outdated:**
- `replicate.run()` for multi-page generation: Still works but blocks — use `async_run()` instead.
- Storing `prediction.output` as a URL string: Returns `FileOutput` in 1.0.7; call `.aread()`.

---

## Sources

### Primary (HIGH confidence)
- Replicate SDK 1.0.7 source — `/home/jeff/Projects/k-kids-books/.venv/lib/python3.13/site-packages/replicate/` — run.py, prediction.py, helpers.py, file.py, exceptions.py, client.py
- Phase 1 research docs — `.planning/research/STACK.md`, `ARCHITECTURE.md`, `PITFALLS.md` — confirmed design decisions

### Secondary (MEDIUM confidence)
- [Replicate Python SDK — GitHub](https://github.com/replicate/replicate-python) — async patterns confirmed
- [FLUX.1 Kontext [pro] on Replicate](https://replicate.com/black-forest-labs/flux-kontext-pro) — model availability, input_image parameter confirmed
- [fal.ai FLUX.1 Kontext Pro](https://fal.ai/models/fal-ai/flux-pro/kontext) — $0.04/image pricing, aspect_ratio enum values
- [BFL Kontext announcement](https://bfl.ai/announcements/flux-1-kontext) — character consistency without fine-tuning
- [Together.ai Flux Kontext blog](https://www.together.ai/blog/flux-1-kontext) — character consistency claims, multi-character stitching guidance
- [apidog.com Flux Kontext API guide](https://apidog.com/blog/how-to-use-flux-kontext-with-apis-a-developers-guide-2/) — SDK usage patterns confirmed

### Tertiary (LOW confidence)
- WebSearch results on full input schema — `safety_tolerance`, `guidance` parameters from third-party API providers; not directly verified on Replicate

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — SDK installed and source-verified
- API surface (async_run, FileOutput, exceptions): HIGH — confirmed from SDK source
- Flux Kontext Pro input parameters: MEDIUM — multi-source WebSearch, not direct API verification
- Flux Kontext Pro output resolution: LOW — not confirmed; requires empirical test
- Pricing: MEDIUM — confirmed $0.04 on fal.ai/BFL; Replicate estimate only

**Research date:** 2026-03-24
**Valid until:** 2026-06-24 (90 days — SDK is stable 1.0.x; Replicate model deployments change more often)
