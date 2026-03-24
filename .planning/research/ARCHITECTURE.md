# Architecture Patterns: BookForge CLI Pipeline

**Domain:** CLI-based bilingual children's book production pipeline
**Researched:** 2026-03-24
**Overall confidence:** HIGH — well-established Python patterns throughout

---

## Recommended Architecture

BookForge is a **linear stage pipeline** with human review gates. Each stage reads from
the previous stage's output and writes to a well-defined project directory. State is
persisted per-project in a JSON file so any command can resume after interruption.

```
┌─────────────────────────────────────────────────────────────────┐
│                        bookforge CLI                            │
│  (Click command group — entry point, no business logic here)    │
└──────────────┬──────────────────────────────────────────────────┘
               │ dispatches to
       ┌───────┼──────────────────────────────────────┐
       ▼       ▼       ▼        ▼         ▼           ▼
    [new]  [story] [illus-  [build]   [review]   [calendar]
            gate   trate]
               │       │        │
               ▼       ▼        ▼
          ┌────────────────────────┐
          │    Project State       │  ← .bookforge/state.json
          │    (per-book dir)      │    tracks stage completion,
          └────────────────────────┘    image status per page
               │
       ┌───────┴────────────────────────┐
       ▼                                ▼
  ┌──────────┐                   ┌────────────┐
  │  Story   │                   │   Image    │
  │  Layer   │                   │   Layer    │
  │(Claude   │                   │ (provider- │
  │   API)   │                   │  agnostic) │
  └──────────┘                   └────────────┘
       │                                │
       └──────────────┬─────────────────┘
                      ▼
              ┌──────────────┐
              │  Build Layer │
              │ (Jinja2 HTML │
              │  + WeasyPrint│
              │    PDF)      │
              └──────────────┘
                      │
                      ▼
              ┌──────────────┐
              │  Publish Pkg │
              │  (zipped     │
              │   assets +   │
              │  listing MD) │
              └──────────────┘
```

---

## Component Boundaries

### 1. CLI Layer (`bookforge/cli/`)

**Responsibility:** Command parsing, argument validation, human review gates, progress
output. Zero business logic — delegates entirely to service layer.

**Communicates with:** All service components via direct Python calls (not subprocess).

**Commands:**

| Command | Triggers |
|---------|----------|
| `new <slug>` | Scaffolds project dir, writes state.json |
| `story [--regenerate]` | StoryService.generate() |
| `illustrate [--redo PAGE]` | ImageService.generate_all() |
| `build [--edition en|ko|bilingual]` | BuildService.assemble_html(), BuildService.export_pdf() |
| `review` | Opens HTML preview in browser, prompts approval |
| `publish` | PublishService.package() |
| `calendar [--year YEAR]` | CalendarService.show() |

Human review gates live in the CLI layer as interactive prompts (Click's `click.confirm`
and `click.pause`). If a gate is not passed, the command exits with a non-zero code and
the state.json stage is NOT advanced.

**Build with:** Click 8.x command groups. Register subcommands via `group.add_command()`
in separate modules so each command file stays focused. Confidence: HIGH.

---

### 2. Project State (`bookforge/state.py`)

**Responsibility:** Atomic read/write of per-project state. Tracks which pipeline stages
are complete, which images succeeded/failed, and review approvals.

**Communicates with:** All service layers (read before acting, write after success).

**State schema (state.json):**

```json
{
  "version": 1,
  "slug": "dangun-story",
  "created_at": "2026-03-24T10:00:00Z",
  "style_guide": "style-guides/korean-cute-watercolor.yaml",
  "stages": {
    "story": "approved",
    "illustrate": "complete",
    "build_en": "complete",
    "build_ko": "pending",
    "build_bilingual": "pending",
    "publish": "pending"
  },
  "pages": {
    "01": {"status": "ok", "image_path": "images/page-01.png"},
    "02": {"status": "failed", "error": "timeout", "image_path": null},
    "03": {"status": "pending", "image_path": null}
  }
}
```

Stage values: `pending` → `complete` → `approved` (story/review stages only add `approved`).

**Pattern:** JSON file with atomic write (write to `.tmp`, then `os.replace()`). No
database needed — at 1 book/month, SQLite overhead is unjustified. Confidence: HIGH.

---

### 3. Story Layer (`bookforge/story/`)

**Responsibility:** Parse existing story markdown, or generate new story via Claude API.
Validate bilingual structure. Write canonical story.md to project dir.

**Communicates with:** State (reads style guide path), Anthropic SDK.

**Sub-components:**

| Module | Role |
|--------|------|
| `parser.py` | Parse story.md → structured `Book` dataclass |
| `generator.py` | Call Claude API, write story.md, prompt for human review |
| `validator.py` | Confirm all pages have EN text, KO text, image prompt |
| `schema.py` | `Book`, `Page`, `BilingualText` dataclasses |

**Story.md canonical format (from POC):**

```markdown
---
title_en: "The Story of Dangun"
title_ko: "단군 이야기"
slug: dangun-story
age_range: "4-8"
pages: 20
style_guide: korean-cute-watercolor
characters: [horang, gomi]
---

<!-- page:01 -->
**EN:** A long time ago...
**KO:** 옛날 옛날에...

> IMAGE: Misty mountain, Ho-rang and Gom-i peek from behind trees...

<!-- page:02 -->
...
```

`python-frontmatter` parses the YAML header; a custom regex-based splitter handles page
boundaries and extracts EN/KO text blocks and image prompts. Confidence: HIGH.

---

### 4. Image Layer (`bookforge/images/`)

**Responsibility:** Generate illustrations with character consistency. Provider-agnostic
interface so Flux Kontext (default), DALL-E 3, or others can be swapped via config.

**Communicates with:** State (reads/writes per-page status), Style Guide, Provider adapters.

**Design — Abstract Provider Interface:**

```python
# bookforge/images/provider.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class ImageRequest:
    prompt: str
    reference_images: list[str]   # local paths to character refs
    width: int
    height: int
    style_prefix: str             # from style guide

@dataclass
class ImageResult:
    path: str
    provider: str
    cost_usd: float

class ImageProvider(ABC):
    @abstractmethod
    def generate(self, request: ImageRequest) -> ImageResult: ...

    @abstractmethod
    def estimated_cost(self, request: ImageRequest) -> float: ...
```

**Concrete providers:**

| Module | Provider | Method |
|--------|----------|--------|
| `providers/flux_kontext.py` | Replicate Flux Kontext [pro] | Image + reference input via Replicate API |
| `providers/flux_dev.py` | Replicate Flux Kontext [dev] | Open-source, cheaper, less consistent |
| `providers/dalle3.py` | OpenAI DALL-E 3 | No character refs — fallback only |

**Provider selection:** Read from `style_guide.yaml` → `image_provider: flux_kontext_pro`.
Factory function `get_provider(name: str) -> ImageProvider` in `providers/__init__.py`.

**Character reference strategy (Flux Kontext):**

Flux Kontext [pro/max] accepts reference images and maintains character consistency across
edits and generations without fine-tuning. Character reference PNGs live in
`style-guides/characters/horang-ref.png` and `gomi-ref.png`. The `ImageRequest` passes
these paths; the provider adapter uploads to Replicate as `input_image` alongside the
page prompt. Confidence: MEDIUM (Kontext character consistency is documented but warrants
testing early — this is the hardest technical risk).

**Resume/retry logic in `ImageService`:**

```
for each page in book:
    if state.pages[page].status == "ok" and not --redo:
        skip (already done)
    if state.pages[page].status == "failed" or --redo PAGE:
        retry
    generate → save to images/ → update state atomically
```

`--redo all` regenerates everything. `--redo 03,07` regenerates only those pages.

---

### 5. Style Guide (`bookforge/style/`)

**Responsibility:** Load and validate YAML style guides that parameterize generation.
Single source of truth for art style, prompt prefixes, characters, color palette,
image dimensions, and provider config.

**Communicates with:** Story Layer (validation), Image Layer (prompt construction),
Build Layer (color tokens for CSS).

**style-guide YAML structure:**

```yaml
name: korean-cute-watercolor
version: 1

art_style:
  prompt_prefix: "Korean watercolor illustration, soft pastel colors, cute rounded characters, Kakao-style, children's picture book, --no photorealistic, --no dark"
  negative_prompt: "photorealistic, dark, scary, adult, text, watermark"
  color_palette: [sandstone, sky_blue, warm_green, peach, soft_gold]

image:
  provider: flux_kontext_pro
  width: 1024
  height: 1024
  aspect_ratio: "1:1"

characters:
  horang:
    name_en: "Ho-rang"
    name_ko: "호랑이"
    description: "cute orange tiger cub, round face, big eyes, small nose"
    reference_image: characters/horang-ref.png
  gomi:
    name_en: "Gom-i"
    name_ko: "곰이"
    description: "cute brown bear cub, chubby cheeks, round ears"
    reference_image: characters/gomi-ref.png

layout:
  trim_inches: [8.5, 8.5]
  bleed_inches: 0.125
  safe_margin_inches: 0.25
  dpi: 300
```

---

### 6. Build Layer (`bookforge/build/`)

**Responsibility:** Assemble HTML from story + images, then export to PDF variants.

**Communicates with:** Story schema (reads `Book` dataclass), Image paths from state,
Style guide (CSS color tokens, dimensions), Jinja2, WeasyPrint.

**Sub-components:**

| Module | Role |
|--------|------|
| `assembler.py` | `Book` → rendered HTML string via Jinja2 |
| `exporter.py` | HTML string → PDF (screen or print variant) |
| `templates/` | Jinja2 templates: `book.html`, `page.html`, `cover.html` |
| `css/` | `screen.css` (RGB), `print.css` (bleed + trim marks + 300dpi) |

**Three editions:** English-only, Korean-only, Bilingual. The assembler receives an
`edition` parameter and selects which text fields to render per page. Same images,
different text visibility. This is a template logic concern — CSS `display:none` on
the unneeded language block, not three separate templates.

**PDF variants:**

| Variant | CSS Profile | Bleed | Color | Purpose |
|---------|-------------|-------|-------|---------|
| Screen | `screen.css` | None | RGB | Gumroad digital download |
| Print | `print.css` | 0.125" | sRGB (ICC embedded) | KDP upload |

WeasyPrint supports CSS Paged Media `@page { bleed: 3.2mm; marks: crop cross; }` for the
print variant. RGB not CMYK — WeasyPrint cannot produce CMYK; KDP accepts sRGB and
converts internally (this is an official KDP-documented acceptable path). Confidence: HIGH.

**Output files per edition:**

```
dist/
  dangun-story-en-screen.pdf
  dangun-story-en-print.pdf
  dangun-story-ko-screen.pdf
  dangun-story-ko-print.pdf
  dangun-story-bilingual-screen.pdf
  dangun-story-bilingual-print.pdf
```

---

### 7. Publish Layer (`bookforge/publish/`)

**Responsibility:** Bundle final PDFs with generated listing copy (title, description,
keywords, pricing recommendation) into a dated zip package ready for manual upload.

**Communicates with:** Build layer outputs (reads dist/), Claude API for listing copy.

**Output:**

```
publish/2026-03-24-dangun-story/
  dangun-story-en-screen.pdf        ← Gumroad
  dangun-story-en-print.pdf         ← KDP interior
  dangun-story-bilingual-screen.pdf ← Gumroad
  listing-gumroad.md                ← title, description, tags, price
  listing-kdp.md                    ← title, subtitle, keywords, categories
  UPLOAD-CHECKLIST.md               ← step-by-step manual upload instructions
```

No API upload. KDP and Gumroad have no public product-creation APIs. This layer is
intentionally thin — a packaging and copy-generation step, not a platform integration.

---

### 8. Calendar Layer (`bookforge/calendar/`)

**Responsibility:** Display upcoming release windows based on holiday calendar. Suggest
deadlines working backwards from publication date (release 2-3 weeks before holiday).

**Communicates with:** nothing external — pure date math + YAML holidays file.

**Implementation:** Simple read of `holidays.yaml`, date arithmetic, Rich table output
in terminal. No database. Confidence: HIGH.

---

## Data Flow

```
User invokes `bookforge new dangun-story`
    │
    ▼
Scaffold: create books/dangun-story/ directory tree
          write state.json (all stages: pending)
          copy style guide reference

User invokes `bookforge story`
    │
    ▼
Story Layer reads: style_guide.yaml, optional existing story.md
Story Layer calls: Claude API → streams story to story.md
CLI prints story, prompts: "Approve for illustration? [y/N]"
    │ approved
    ▼
State updated: stages.story = "approved"

User invokes `bookforge illustrate`
    │
    ▼
Image Layer reads: story.md (via parser), style_guide.yaml, state.json
For each page (skip if state.pages[N].status == "ok"):
    Build ImageRequest (page prompt + style prefix + character refs)
    Call provider.generate() → save PNG to images/
    Update state.pages[N] atomically
CLI prints progress bar (Rich)
    │ all pages done (or partial — can re-run)
    ▼
State updated: stages.illustrate = "complete"

User invokes `bookforge build`
    │
    ▼
Build Layer reads: story.md, images/*.png, style_guide.yaml
Assembler renders: Jinja2 → HTML (all 3 editions)
Exporter renders: HTML → PDF x6 (3 editions × 2 formats)
PDFs written to: dist/
    │
    ▼
State updated: stages.build_* = "complete"

User invokes `bookforge review`
    │
    ▼
CLI opens dist/dangun-story-bilingual-screen.pdf in browser
CLI prompts: "Approve for publishing? [y/N]"
    │ approved
    ▼
State updated: stages.publish = "approved"

User invokes `bookforge publish`
    │
    ▼
Publish Layer reads: dist/*.pdf, state.json
Calls Claude API: generate listing copy
Bundles: zipped publish package
    │
    ▼
CLI prints: "Package ready: publish/2026-03-24-dangun-story.zip"
             "See UPLOAD-CHECKLIST.md for next steps"
```

---

## Project Directory Structure

```
books/
  dangun-story/
    story.md              ← canonical story source
    state.json            ← pipeline state
    images/
      page-01.png
      page-02.png
      ...
    dist/
      *-screen.pdf
      *-print.pdf
    publish/
      2026-03-24/
        ...

style-guides/
  korean-cute-watercolor.yaml
  characters/
    horang-ref.png
    gomi-ref.png

bookforge/
  cli/
    __init__.py           ← Click group registration
    new.py
    story.py
    illustrate.py
    build.py
    review.py
    publish.py
    calendar.py
  story/
    parser.py
    generator.py
    validator.py
    schema.py
  images/
    service.py
    provider.py           ← ABC
    providers/
      flux_kontext.py
      flux_dev.py
      dalle3.py
  style/
    loader.py
    validator.py
  build/
    assembler.py
    exporter.py
    templates/
    css/
  publish/
    packager.py
    listing.py
  calendar/
    service.py
    holidays.yaml
  state.py
  config.py               ← env vars (API keys, default paths)
```

---

## Suggested Build Order

The pipeline has hard dependencies. Build bottom-up:

**Phase 1 — Foundation (no external dependencies)**
1. `state.py` — project state read/write (atomic JSON)
2. `story/schema.py` — `Book`, `Page`, `BilingualText` dataclasses
3. `story/parser.py` — parse story.md → `Book` (testable with POC file)
4. `style/loader.py` — load and validate style guide YAML
5. `cli/__init__.py` + `cli/new.py` — scaffold project dirs

This gives you a working `bookforge new` and the ability to parse the Dangun POC story
immediately. All subsequent phases can be tested with real data from day one.

**Phase 2 — Story Generation**
6. `story/generator.py` — Claude API call → story.md
7. `story/validator.py` — check bilingual completeness
8. `cli/story.py` + review gate

Human review gate for Korean text (wife's proofreading step) lives here.

**Phase 3 — Image Generation (highest technical risk)**
9. `images/provider.py` — abstract base class
10. `images/providers/flux_kontext.py` — Replicate integration
11. `images/service.py` — retry/resume logic
12. `cli/illustrate.py`

Build and validate character consistency here before proceeding. This is the most
uncertain component. If Flux Kontext [pro] character refs are not consistent enough,
the mitigation is fine-tuning (LoRA via Replicate) — defer that decision until you
have test images.

**Phase 4 — Build and PDF**
13. `build/templates/` — Jinja2 page templates
14. `build/css/` — screen and print CSS
15. `build/assembler.py` — Book → HTML
16. `build/exporter.py` — HTML → PDF (WeasyPrint)
17. `cli/build.py`

Verify KDP print PDF compliance (bleed, trim, 300dpi) with KDP's online previewer
before treating this phase as done.

**Phase 5 — Publish and Calendar**
18. `publish/packager.py` + `publish/listing.py`
19. `cli/publish.py` + `cli/review.py`
20. `calendar/service.py` + `cli/calendar.py`

**Phase 6 — Additional providers (if needed)**
21. `images/providers/flux_dev.py` — cheaper option
22. `images/providers/dalle3.py` — fallback

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Business Logic in CLI Layer
**What it looks like:** Putting story generation, image calls, or file I/O directly in
Click command functions.
**Why bad:** Untestable without invoking the CLI. Commands become 200-line functions.
**Instead:** CLI layer only validates args, calls service layer, handles human prompts,
and formats output. All logic lives in service modules.

### Anti-Pattern 2: State in Memory Across Commands
**What it looks like:** Storing pipeline state in a global dict or Click context object.
**Why bad:** Each CLI invocation is a new process. State dies with the process.
**Instead:** Every command reads state.json on startup, writes atomically on success.

### Anti-Pattern 3: Generating All Images Before Any Succeed
**What it looks like:** Batch-submitting all 20 page image requests, then checking results.
**Why bad:** A prompt or style issue on page 1 will waste money on pages 2-20.
**Instead:** Generate sequentially (or in small batches of 3-4), update state per page,
stop on repeated failures and surface the error immediately.

### Anti-Pattern 4: Hardcoded Image Dimensions and Bleed
**What it looks like:** `width = 1024`, `bleed = "3.2mm"` scattered across assembler,
exporter, and CSS.
**Why bad:** KDP trim sizes change; children's books sometimes need different formats.
**Instead:** All layout constants flow from `style_guide.yaml` → `StyleGuide` dataclass
→ injected into templates and CSS via template variables.

### Anti-Pattern 5: Three Separate Templates per Edition
**What it looks like:** `book-en.html`, `book-ko.html`, `book-bilingual.html`.
**Why bad:** Any layout change requires three edits.
**Instead:** One template, `edition` parameter controls CSS visibility of EN/KO text
blocks. `{{ page.text.en if edition in ['en', 'bilingual'] else '' }}`.

---

## Scalability Considerations

This is a 1-book/month tool for two people. Do not over-architect.

| Concern | At current scale | If demand grows |
|---------|-----------------|-----------------|
| Image generation | Sequential, synchronous | Add `asyncio` + concurrent Replicate calls |
| Book count | Files in `books/` dir | Still fine at 100 books |
| Multiple style guides | Already supported | Already supported |
| Multiple series | New style guide per series | Already supported |
| Automation / no human gates | Out of scope | Add `--approve` flags later |

---

## Sources

- Click advanced patterns: [Click Documentation — Commands and Groups](https://click.palletsprojects.com/en/stable/commands/)
- Flux Kontext character consistency: [Generate consistent characters — Replicate blog](https://replicate.com/blog/generate-consistent-characters)
- Flux Kontext API: [FLUX.1 Kontext models — Together AI](https://www.together.ai/blog/flux-1-kontext)
- WeasyPrint bleed/trim support: [WeasyPrint official site](https://weasyprint.org/)
- KDP bleed specification: [KDP Set Trim Size, Bleed, and Margins](https://kdp.amazon.com/en_US/help/topic/GVBQ3CMEQW3W2VL6)
- KDP cover requirements: [KDP Create a Paperback Cover](https://kdp.amazon.com/en_US/help/topic/G201953020)
- Python frontmatter parsing: [python-frontmatter PyPI](https://pypi.org/project/python-frontmatter/)
- Adapter pattern for provider abstraction: [Adapter Design Pattern — Refactoring Guru](https://refactoring.guru/design-patterns/adapter/python/example)
- Atomic checkpoint pattern: [Resumable pipeline with SQLite — SeaQL blog](https://www.sea-ql.org/blog/2026-02-28-sea-orm-sync/)
