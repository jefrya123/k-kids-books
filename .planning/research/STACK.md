# Technology Stack

**Project:** BookForge — Bilingual Korean Children's Book Pipeline
**Researched:** 2026-03-24
**Research Mode:** Ecosystem (Stack dimension)

---

## Recommended Stack

### CLI Framework

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Typer | 0.24.1 | Command definitions, subcommands, argument/option parsing | Built on Click but uses Python type hints — no decorators, less boilerplate. Auto-generates `--help`. Natural fit for `new`, `illustrate`, `build`, `review`, `publish`, `calendar` command structure. Actively maintained, 0.24.x released 2026. |
| Rich | 14.3.3 | Terminal output, progress bars, review prompts | Human review gates need interactive prompts and progress display. Rich + Typer integrate cleanly (Typer uses Rich under the hood for pretty help). Best-in-class terminal UI for Python. |

**Confidence:** HIGH — verified against PyPI current versions.

**Why not Click directly:** Typer is Click with type hints; less ceremony for a project this size. No reason to drop down to raw Click.

---

### Story Generation

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| anthropic | 0.86.0 | Claude API for bilingual story generation | First-party SDK. Supports streaming (good for long-form story output), structured output via tool use (useful for enforcing YAML frontmatter + bilingual block format), and the latest Claude Sonnet/Opus models. |

**Confidence:** HIGH — verified PyPI. Claude is the specified requirement.

**Model choice:** Use `claude-sonnet-4-5` for story generation (best cost/quality for structured text tasks) with `claude-opus-4-5` as override flag for difficult prompts. Pin via config, not code.

**Why not LangChain:** No need. LangChain adds abstraction overhead for what is a single-provider, single-task use case. Direct SDK is simpler, debuggable, and future-proof.

---

### Image Generation

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| replicate | 1.0.7 | Provider-agnostic image generation via Flux Kontext | Official Replicate SDK hit 1.0 milestone (stable API). Hosts `black-forest-labs/flux-kontext-pro` and `flux-kontext-max`. Supports async predictions via `async_run()` — critical for generating 20 page illustrations without blocking. |
| httpx | 0.28.1 | Direct API calls for non-Replicate providers (future) | Async-native HTTP client. When the provider-agnostic interface eventually needs to call Together.ai, Runware, or other Flux hosts directly, httpx handles concurrent polling cleanly. Replicate SDK itself uses httpx internally. |
| Pillow | 12.1.1 | Image validation, resize, sRGB conversion, thumbnail generation | Verify downloaded images are valid, correct DPI metadata, generate review thumbnails. Version 12.x is current. |

**Confidence:** HIGH for replicate SDK (PyPI verified, 1.0.7 stable). MEDIUM for Flux Kontext character consistency claims (WebSearch only, though Together.ai blog cites 90-95% fidelity with reference images).

**Flux Kontext model choice:** `black-forest-labs/flux-kontext-pro` as default. Supports up to 10 reference images for character consistency — this directly addresses the hardest constraint (Ho-rang and Gom-i looking the same across pages). `flux-kontext-max` available as `--quality max` flag for cover art.

**Provider abstraction pattern:**
```python
class ImageProvider(Protocol):
    async def generate(self, prompt: str, ref_images: list[Path], **kwargs) -> Path: ...
```
Concrete implementations: `ReplicateProvider`, future `TogetherProvider`. Swap via `style_guide.yaml` `image_provider:` field, not code changes.

**Why not DALL-E 3:** No reference image / IP-Adapter support. Character consistency is impossible without it. Confirmed in PROJECT.md as a decided decision.

**Why not Stability AI directly:** Replicate provides a unified billing and API surface across providers. At $0.04–1.00/image and ~20 images/book, staying under the $15 budget is manageable on Replicate's pay-per-second model.

---

### Story File Parsing

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| python-frontmatter | 1.1.0 | Parse YAML frontmatter from story `.md` files | Clean API: `frontmatter.load(path)` returns metadata dict + content. Handles the story markdown format specified in PROJECT.md. Current (1.1.0). |
| ruamel.yaml | 0.19.1 | Read/write style_guide YAML files | Preserves comments in YAML round-trips — important so `bookforge new` scaffolding comments survive subsequent edits to `style_guide.yaml`. PyYAML does not preserve comments. |

**Confidence:** HIGH — PyPI verified. Standard combination for comment-preserving YAML pipelines.

**Why not PyYAML for style guides:** `yaml.dump()` strips all comments from YAML files. A style guide is a human-edited artifact; preserving comments is not optional.

---

### HTML Templating

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Jinja2 | 3.1.6 | Book page HTML templates | De facto standard for Python HTML generation. Supports template inheritance (base layout → page template), filters (for Korean/English text switching), and macros (reusable spread components). Already installed in most Python environments. |

**Confidence:** HIGH — PyPI verified. Standard choice, no credible alternative.

**Template strategy:** One base `book.html.j2` that both screen and print editions extend. Print template adds `@page { bleed: 0.125in; }` via CSS. Three edition variants (English, Korean, Bilingual) are Jinja2 template conditionals, not separate templates.

---

### PDF Generation

This is the most complex stack decision. The pipeline requires two distinct PDF outputs with different constraints:

| Output | Dimensions | Bleed | Marks | Color | Purpose |
|--------|-----------|-------|-------|-------|---------|
| Screen | 8.5×8.5" | None | None | sRGB | Gumroad digital download |
| Print | 8.625×8.75" | 0.125" all sides | None (KDP rejects marks) | sRGB + OutputIntent | KDP interior upload |

**KDP critical finding:** KDP *rejects* PDFs with visible crop/trim marks. The file dimensions must include the bleed area (8.625×8.75"), but marks must not appear in the PDF. OutputIntent with sRGB ICC profile is best practice for print color consistency.

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| WeasyPrint | 68.1 | HTML→PDF rendering for both screen and print | Pure Python (no headless browser), supports CSS `@page` with `bleed`, `marks: none`, trim box/bleed box metadata injection. Actively maintained (68.1 released 2025/2026). No JS needed — our templates are static HTML+CSS. |
| pikepdf | 10.5.1 | Post-process print PDF: embed sRGB ICC OutputIntent, set MediaBox/TrimBox/BleedBox | WeasyPrint sets bleed box metadata but has known bugs with background color extending into bleed area. pikepdf patches the PDF after WeasyPrint renders it — embed ICC profile, correct box geometry, verify no marks are present. QPDF-backed, low-level, reliable. |

**Confidence:** HIGH for WeasyPrint (PyPI verified, widely used for invoice/report PDFs). MEDIUM for the WeasyPrint + pikepdf two-pass approach (based on verified WeasyPrint bleed limitation; pikepdf's ICC output intent support confirmed via GitHub issue #509 — but integration is custom code we write, not a pre-built solution).

**Why not Playwright/headless Chromium:** Correct output, but adds a 120MB+ system dependency, requires a running browser process, and is overkill for static HTML. Our templates have zero JavaScript. WeasyPrint is 10x faster to install and produces smaller binaries.

**Why not ReportLab:** Requires building page layouts programmatically in Python. We already have Jinja2 HTML templates that are easier to design, preview in a browser, and iterate on. HTML→PDF via WeasyPrint is the right abstraction for a visually designed book.

**Why not fpdf2:** Less mature CSS support than WeasyPrint. fpdf2's Jinja integration is a second-class feature; WeasyPrint is the primary use case.

**Print PDF post-processing with pikepdf:**
```python
# After WeasyPrint renders print.pdf:
# 1. Open with pikepdf
# 2. Set /MediaBox to bleed dimensions (8.625" × 8.75" in points)
# 3. Set /TrimBox to trim dimensions (8.5" × 8.5" in points)
# 4. Set /BleedBox = /MediaBox
# 5. Embed sRGB ICC profile as /OutputIntent
# 6. Save linearized (web-optimized) PDF
```

**sRGB ICC source:** Download `sRGB_v4_ICC_preference.icc` from ICC.org and ship it in `bookforge/assets/`. This is the reference sRGB profile used by Adobe and ICC. Embed once at build time.

---

### Configuration and Data Models

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Pydantic | 2.12.5 | Validate style guide YAML, story frontmatter, CLI config | v2 is the current standard. Type-safe validation with clear error messages at load time — better than discovering malformed config mid-pipeline. Dataclass-compatible. |

**Confidence:** HIGH — PyPI verified. Pydantic v2 is the 2025/2026 standard for Python config validation.

**Model example:**
```python
class StyleGuide(BaseModel):
    art_style: str
    characters: dict[str, CharacterDef]
    color_palette: list[str]
    prompt_prefix: str
    image_provider: str = "replicate/flux-kontext-pro"
```

---

### Project Management and Persistence

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Python stdlib `pathlib` | N/A | All file operations | No external dependency needed. Pathlib is clean and sufficient for a pipeline that reads `.md` files and writes to `output/` directories. |
| Python stdlib `json` | N/A | State files (which pages are complete, retry state) | Simple key/value store for image generation state (`pages_complete: [1,3,5,...]`). No database needed at 1 book/month. Flat JSON file in the book project directory. |

**Why not SQLite:** Overkill. The state is at most 20 records per book. A `state.json` file per project is inspectable, diffable, and Git-friendly.

---

### Testing

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| pytest | Current | Unit and integration tests | Project standard per CLAUDE.md. |
| pytest-asyncio | Current | Test async image generation code | Replicate SDK uses async; tests must support it. |
| responses / respx | Current | Mock HTTP calls to Replicate/Anthropic APIs | Tests must not hit live APIs. `respx` mocks httpx calls; `responses` mocks requests. Use `respx` since we're in the httpx ecosystem. |

---

### Packaging

| Technology | Purpose | Why |
|------------|---------|-----|
| `pyproject.toml` + `uv` | Dependency management and CLI entry point | Project uses `uv run` per CLAUDE.md. Define entry point as `bookforge = "bookforge.cli:app"` in `[project.scripts]`. `uv` handles venv and dependency resolution. |

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| CLI | Typer 0.24.1 | Click | Typer is Click with type hints; less boilerplate for same capability |
| CLI | Typer 0.24.1 | argparse | argparse has no subcommand UX, no auto-complete, no Rich integration |
| Image gen | replicate 1.0.7 | stability-sdk (direct) | Replicate unifies billing, has Flux Kontext; direct Stability doesn't have Kontext |
| Image gen | Flux Kontext | DALL-E 3 | DALL-E 3 has no reference image support; character consistency is impossible |
| PDF | WeasyPrint | Playwright/Chromium | 120MB browser dependency; zero JS in our templates; WeasyPrint is 10x simpler |
| PDF | WeasyPrint | ReportLab | ReportLab requires programmatic layout; we have HTML templates that render in browser |
| PDF post-proc | pikepdf | pypdf | pikepdf has lower-level PDF box manipulation and verified ICC OutputIntent via QPDF |
| YAML | ruamel.yaml | PyYAML | PyYAML destroys comments on round-trip; style guides are human-edited |
| Config | Pydantic v2 | dataclasses | Pydantic gives validation errors with field names and types, not cryptic AttributeErrors |
| Story parsing | python-frontmatter | manual regex | python-frontmatter handles edge cases in YAML frontmatter; no need to reinvent |

---

## Installation

```bash
# Core runtime dependencies
uv add anthropic replicate jinja2 weasyprint pikepdf \
       pillow pydantic "ruamel.yaml" python-frontmatter \
       typer rich httpx

# Dev dependencies
uv add --dev pytest pytest-asyncio respx
```

**System dependencies for WeasyPrint (Debian/Ubuntu):**
```bash
sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0
```
WeasyPrint uses Pango for text layout and font rendering. These are the only non-Python system deps in the stack.

---

## Pinned Version Summary

| Package | Pinned Version | Verified Via |
|---------|---------------|-------------|
| anthropic | >=0.86.0 | PyPI (2026-03-24) |
| replicate | >=1.0.7 | PyPI (2026-03-24) |
| weasyprint | >=68.1 | PyPI (2026-03-24) |
| pikepdf | >=10.5.1 | PyPI (2026-03-24) |
| typer | >=0.24.1 | PyPI (2026-03-24) |
| rich | >=14.3.3 | PyPI (2026-03-24) |
| jinja2 | >=3.1.6 | PyPI (2026-03-24) |
| pillow | >=12.1.1 | PyPI (2026-03-24) |
| pydantic | >=2.12.5 | PyPI (2026-03-24) |
| ruamel.yaml | >=0.19.1 | PyPI (2026-03-24) |
| python-frontmatter | >=1.1.0 | PyPI (2026-03-24) |
| httpx | >=0.28.1 | PyPI (2026-03-24) |

Use `>=` lower bounds in `pyproject.toml` (not exact pins) to allow security patches. Lock with `uv lock` for reproducible builds.

---

## Open Questions / Flags for Later Phases

1. **WeasyPrint bleed rendering bug**: Background images and colors are known to not properly extend into the bleed area in some WeasyPrint versions. The pikepdf post-processing step patches box geometry, but visual bleed content (illustration bleeding to page edge) needs testing. Mitigation: design illustrations with 0.125" safe zone or test WeasyPrint 68.1 specifically.

2. **Flux Kontext character fidelity at scale**: The 90-95% fidelity claim (Together.ai blog, WebSearch only) needs empirical validation on the actual Ho-rang and Gom-i style. Reserve Phase 1 spike to test 3-5 pages before committing to the full pipeline.

3. **Korean font embedding in WeasyPrint**: WeasyPrint uses Pango for font rendering. Korean text requires a Korean font (e.g., Noto Sans KR) to be installed on the system or embedded via `@font-face` in CSS. This is a known setup step, not a blocker, but must be documented in the install guide.

4. **Replicate async polling**: `replicate.async_run()` is available in 1.0.x but the exact polling/webhook API should be confirmed against the 1.0.7 changelog before building the concurrency layer.

---

## Sources

- [anthropic PyPI](https://pypi.org/project/anthropic/) — version 0.86.0 confirmed
- [replicate PyPI](https://pypi.org/project/replicate/) — version 1.0.7 confirmed
- [WeasyPrint PyPI](https://pypi.org/project/weasyprint/) — version 68.1 confirmed
- [WeasyPrint Going Further docs](https://doc.courtbouillon.org/weasyprint/stable/going_further.html) — bleed/marks CSS support
- [WeasyPrint bleed bug #934](https://github.com/Kozea/WeasyPrint/issues/934) — background-in-bleed limitation
- [pikepdf ICC OutputIntent issue #509](https://github.com/pikepdf/pikepdf/issues/509) — confirmed ICC embedding support
- [FLUX.1 Kontext on Replicate](https://replicate.com/black-forest-labs/flux-kontext-dev) — model availability
- [Together.ai Kontext blog](https://www.together.ai/blog/flux-1-kontext) — character consistency claims (MEDIUM confidence, single source)
- [KDP Bleed/Trim size spec](https://kdp.amazon.com/en_US/help/topic/GVBQ3CMEQW3X2VL6) — 0.125" bleed, 8.625×8.75" PDF for 8.5×8.5" trim
- [KDP Paperback submission guidelines](https://kdp.amazon.com/en_US/help/topic/G201857950) — no crop marks requirement
- [Typer alternatives page](https://typer.tiangolo.com/alternatives/) — confirms Click relationship
- [dantebytes WeasyPrint + Jinja2](https://dantebytes.com/generating-pdfs-from-html-with-weasyprint-and-jinja2-python/) — pattern confirmation
