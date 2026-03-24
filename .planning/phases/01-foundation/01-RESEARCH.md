# Phase 1: Foundation - Research

**Researched:** 2026-03-24
**Domain:** Python CLI scaffolding, story file format parsing, style guide loading, Pydantic data modeling
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CLI-01 | `uv run bookforge new <slug>` scaffolds a new book directory with story.md template | Typer `@app.command()` pattern; pathlib for directory creation; `python-frontmatter` for template writing |
| STOR-01 | Story markdown with YAML frontmatter (title, title_ko, slug, trim_size, price, ages) | `python-frontmatter 1.1.0` — `frontmatter.load()` returns metadata dict + content body |
| STOR-02 | Page boundaries defined by `## Page N` headers | Regex split on `^## Page \d+` after frontmatter is stripped; see parser pattern below |
| STOR-03 | English bare, Korean wrapped in `<!-- ko --> / <!-- /ko -->` | Regex extraction: `<!--\s*ko\s*-->(.*?)<!--\s*/ko\s*-->` (DOTALL) |
| STOR-04 | Image prompts embedded as `<!-- image: ... -->` per page | Regex: `<!--\s*image:\s*(.*?)\s*-->` |
| STOR-05 | Claude API generates bilingual draft story from one-line prompt via `new` command | `anthropic 0.86.0` SDK; streaming response; system prompt enforces story.md format |
| STOR-06 | Image prompt overrides saved as `<!-- image-override: ... -->` when using `--redo --prompt` | Pydantic `Page` model with `image_override: str | None`; parser checks override before prompt |
| STYL-01 | Style guide YAML: art_style, colors, characters, negative_prompt | `ruamel.yaml 0.19.1` round-trip load; Pydantic `StyleGuide` model validates required fields |
| STYL-02 | Character definitions with visual description and reference image paths | Pydantic `CharacterDef` model nested in `StyleGuide.characters` dict |
| STYL-03 | Ho-rang and Gom-i character sheets generated upfront as reference images | Phase 1 responsibility: define character defs + scaffold placeholder reference image paths; actual generation is Phase 2 |
| STYL-04 | Every image generation call prepends style prefix + character descriptions + negative prompt | `StyleGuide.build_prompt_prefix(characters)` method returns assembled string — tested here, used in Phase 2 |
| STYL-05 | Image provider configured in style guide YAML | `StyleGuide.image.provider` field; validated by Pydantic against allowed enum values |
</phase_requirements>

---

## Summary

Phase 1 establishes the entire project foundation: the Python package structure, the `bookforge new <slug>` CLI command, the story.md file format with its parser and Pydantic data models, the style guide YAML loader, and a Claude API story generator. No image generation occurs in this phase — that is Phase 2.

The core technical challenge is the story.md format. The POC file (`poc/dangun-book.md`) uses a plain prose format, but the canonical pipeline format uses YAML frontmatter + `## Page N` section headers + inline HTML comments for Korean text and image prompts. Phase 1 must define this format precisely and implement a parser that turns it into a validated `Book` Pydantic model. The `bookforge new` command scaffolds the directory tree, writes a template story.md, copies the default style guide, and calls Claude to generate a draft story — then writes the Claude output to story.md.

The style guide loader uses `ruamel.yaml` (not PyYAML) because style guides are human-edited YAML files with comments that must survive round-trips. The `StyleGuide` Pydantic model validates all required fields on load. The project has no `pyproject.toml` yet — Phase 1 must create it from scratch with the `bookforge` entry point and all Phase 1 runtime dependencies.

**Primary recommendation:** Build bottom-up: `pyproject.toml` → Pydantic schemas → story parser → style guide loader → state module → CLI `new` command + Claude generator. Each layer is testable independently.

---

## Standard Stack

### Core (Phase 1 only)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| typer | >=0.24.1 | CLI command definitions, subcommands, `--help` auto-generation | Click with type hints; less boilerplate. Verified installed (0.24.0 already present in environment). |
| rich | >=14.3.3 | Terminal output, progress feedback during generation | Typer uses Rich internally; zero extra cost |
| anthropic | >=0.86.0 | Claude API for bilingual story generation | First-party SDK; streaming support for long story output |
| python-frontmatter | >=1.1.0 | Parse YAML frontmatter from story.md | Clean `frontmatter.load(path)` API; handles edge cases |
| ruamel.yaml | >=0.19.1 | Read/write style guide YAML preserving comments | PyYAML strips all comments on round-trip — unacceptable for human-edited style guides |
| pydantic | >=2.12.5 | Validate all data models (Book, Page, StyleGuide) | v2 standard; clear error messages at load time. Already installed (2.12.5 confirmed). |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pathlib (stdlib) | N/A | All file path operations | Used everywhere; no external dep needed |
| json (stdlib) | N/A | state.json read/write | Simple; no database needed at this scale |
| re (stdlib) | N/A | Page section splitting, HTML comment extraction | Story parser; no external parser needed |
| pytest | current | Unit tests | Project standard per CLAUDE.md |
| pytest-asyncio | current | Test async Claude streaming | Anthropic SDK uses async |
| respx | current | Mock httpx/Anthropic API calls in tests | Tests must not hit live APIs |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| ruamel.yaml | PyYAML | PyYAML destroys YAML comments on dump — style guides are human-edited, comments are documentation |
| python-frontmatter | manual regex split on `---` | python-frontmatter handles edge cases (YAML strings, nested dicts, multiline values) |
| Pydantic v2 | dataclasses | Pydantic gives field-name error messages with types at validation time, not cryptic AttributeErrors |

**Installation:**
```bash
# From project root (creates pyproject.toml first)
uv init --name bookforge --python ">=3.11"
uv add typer rich anthropic "python-frontmatter" "ruamel.yaml" pydantic
uv add --dev pytest pytest-asyncio respx
```

Note: `replicate`, `weasyprint`, `pikepdf`, `pillow`, `httpx`, `jinja2` are NOT Phase 1 dependencies. Add them in their respective phases.

---

## Architecture Patterns

### Recommended Project Structure (Phase 1 scope)

```
bookforge/               # Python package root
├── __init__.py
├── cli/
│   ├── __init__.py      # Typer app group; registers subcommands
│   └── new.py           # `bookforge new <slug>` command
├── story/
│   ├── __init__.py
│   ├── schema.py        # Book, Page, BilingualText Pydantic models
│   ├── parser.py        # story.md -> Book
│   ├── generator.py     # Claude API -> story.md draft
│   └── validator.py     # Check all pages have EN, KO, image prompt
├── style/
│   ├── __init__.py
│   ├── schema.py        # StyleGuide, CharacterDef Pydantic models
│   └── loader.py        # ruamel.yaml load + validate
├── state.py             # Atomic read/write of state.json
└── config.py            # Env var loading (ANTHROPIC_API_KEY, paths)

books/                   # Created at runtime by `bookforge new`
style-guides/
├── korean-cute-watercolor.yaml
└── characters/
    ├── horang-ref.png   # Placeholder until Phase 2 generates it
    └── gomi-ref.png

pyproject.toml
tests/
├── conftest.py
├── test_story_parser.py
├── test_style_loader.py
├── test_state.py
└── test_new_command.py
```

### Pattern 1: story.md Canonical Format

The POC file (`poc/dangun-book.md`) uses an informal prose format. The pipeline needs a machine-parseable format. These are not the same — Phase 1 defines the canonical format the generator writes and the parser reads.

```markdown
---
title: "The Story of Dangun"
title_ko: "단군 이야기"
slug: dangun-story
trim_size: "8.5x8.5"
price: 4.99
ages: "4-8"
style_guide: korean-cute-watercolor
---

## Page 1

A long time ago...

<!-- ko -->
옛날 옛날에...
<!-- /ko -->

<!-- image: Misty mountain, soft watercolor style, Ho-rang and Gom-i peek from behind trees -->

## Page 2

Hwanin was the King of Heaven.

<!-- ko -->
환인은 하늘의 왕이었어요.
<!-- /ko -->

<!-- image: Kind prince in flowing robes standing on clouds, looking down at earth below -->
```

Key decisions in this format:
- `## Page N` (not `<!-- page:N -->` as shown in ARCHITECTURE.md) — simpler to split with `re.split(r'^## Page \d+', content, flags=re.MULTILINE)`
- Korean in `<!-- ko --> / <!-- /ko -->` (not `**KO:**` prefix) — matches REQUIREMENTS.md STOR-03 verbatim
- Image prompt in `<!-- image: ... -->` (not `> IMAGE:`) — matches REQUIREMENTS.md STOR-04

Note: The ARCHITECTURE.md shows `<!-- page:01 -->` syntax but REQUIREMENTS.md says `## Page N` headers. REQUIREMENTS.md is authoritative — use `## Page N`.

### Pattern 2: Pydantic Story Schema

```python
# bookforge/story/schema.py
from pydantic import BaseModel, field_validator

class BilingualText(BaseModel):
    en: str
    ko: str

class Page(BaseModel):
    number: int
    text: BilingualText
    image_prompt: str
    image_override: str | None = None   # STOR-06

    def effective_prompt(self) -> str:
        """Return override if set, else original prompt."""
        return self.image_override or self.image_prompt

class BookMeta(BaseModel):
    title: str
    title_ko: str
    slug: str
    trim_size: str = "8.5x8.5"
    price: float
    ages: str
    style_guide: str

class Book(BaseModel):
    meta: BookMeta
    pages: list[Page]

    @field_validator("pages")
    @classmethod
    def must_have_pages(cls, v: list[Page]) -> list[Page]:
        if not v:
            raise ValueError("Book must have at least one page")
        return v
```

### Pattern 3: Style Guide Schema

```python
# bookforge/style/schema.py
from pydantic import BaseModel
from pathlib import Path

class CharacterDef(BaseModel):
    name_en: str
    name_ko: str
    description: str          # exact prompt tokens — treated as code, not prose
    reference_image: str      # relative path from style-guides/ dir

class ArtStyle(BaseModel):
    prompt_prefix: str
    negative_prompt: str
    color_palette: list[str]

class ImageConfig(BaseModel):
    provider: str = "flux_kontext_pro"
    width: int = 1024
    height: int = 1024

class Layout(BaseModel):
    trim_inches: list[float] = [8.5, 8.5]
    bleed_inches: float = 0.125
    safe_margin_inches: float = 0.25
    dpi: int = 300

class StyleGuide(BaseModel):
    name: str
    version: int = 1
    art_style: ArtStyle
    image: ImageConfig = ImageConfig()
    characters: dict[str, CharacterDef]
    layout: Layout = Layout()

    def build_prompt_prefix(self) -> str:
        """Assemble full prompt prefix for image generation (STYL-04)."""
        char_descs = "; ".join(
            f"{c.name_en}: {c.description}"
            for c in self.characters.values()
        )
        return f"{self.art_style.prompt_prefix}. Characters: {char_descs}. --no {self.art_style.negative_prompt}"
```

### Pattern 4: Story Parser

```python
# bookforge/story/parser.py
import re
import frontmatter
from bookforge.story.schema import Book, BookMeta, Page, BilingualText

def parse_story(path: str | Path) -> Book:
    post = frontmatter.load(str(path))
    meta = BookMeta(**post.metadata)

    # Split on ## Page N headers
    sections = re.split(r'^## Page \d+\s*$', post.content, flags=re.MULTILINE)
    sections = [s.strip() for s in sections if s.strip()]

    pages = []
    for i, section in enumerate(sections, start=1):
        en_text = _extract_en(section)
        ko_text = _extract_ko(section)
        image_prompt = _extract_image(section)
        image_override = _extract_image_override(section)
        pages.append(Page(
            number=i,
            text=BilingualText(en=en_text, ko=ko_text),
            image_prompt=image_prompt,
            image_override=image_override,
        ))

    return Book(meta=meta, pages=pages)

def _extract_en(text: str) -> str:
    # English is bare text — remove all HTML comment blocks and strip
    clean = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    return clean.strip()

def _extract_ko(text: str) -> str:
    match = re.search(r'<!--\s*ko\s*-->(.*?)<!--\s*/ko\s*-->', text, re.DOTALL)
    return match.group(1).strip() if match else ""

def _extract_image(text: str) -> str:
    match = re.search(r'<!--\s*image:\s*(.*?)\s*-->', text, re.DOTALL)
    return match.group(1).strip() if match else ""

def _extract_image_override(text: str) -> str | None:
    match = re.search(r'<!--\s*image-override:\s*(.*?)\s*-->', text, re.DOTALL)
    return match.group(1).strip() if match else None
```

### Pattern 5: Atomic State Write

```python
# bookforge/state.py
import json
import os
from pathlib import Path

def load_state(book_dir: Path) -> dict:
    state_path = book_dir / "state.json"
    if not state_path.exists():
        return {}
    return json.loads(state_path.read_text())

def save_state(book_dir: Path, state: dict) -> None:
    """Atomic write: write to .tmp then os.replace() to avoid corruption."""
    state_path = book_dir / "state.json"
    tmp_path = state_path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(state, indent=2, default=str))
    os.replace(tmp_path, state_path)
```

### Pattern 6: Typer App Entry Point

```python
# bookforge/cli/__init__.py
import typer
from bookforge.cli.new import new_command

app = typer.Typer(
    name="bookforge",
    help="Bilingual children's book production pipeline.",
    no_args_is_help=True,
)
app.command("new")(new_command)
# Phase 2+: app.command("story")(story_command), etc.
```

```toml
# pyproject.toml [project.scripts]
[project.scripts]
bookforge = "bookforge.cli:app"
```

### Pattern 7: Claude Story Generation

```python
# bookforge/story/generator.py
import anthropic

SYSTEM_PROMPT = """You are a children's book author writing bilingual English/Korean picture books.
Write a story in the exact bookforge story.md format:
- YAML frontmatter with title, title_ko, slug, trim_size, price, ages, style_guide fields
- Pages separated by ## Page N headers (starting at 1)
- English text bare (no markers)
- Korean text wrapped in <!-- ko --> / <!-- /ko --> blocks
- One <!-- image: [description] --> comment per page describing the illustration
Write {page_count} pages. Keep English simple (age {ages}). Korean should be grammatically natural.
"""

def generate_story(prompt: str, style_guide_name: str, page_count: int = 12, ages: str = "4-8") -> str:
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

    with client.messages.stream(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        system=SYSTEM_PROMPT.format(page_count=page_count, ages=ages),
        messages=[{"role": "user", "content": f"Write a children's book about: {prompt}\nStyle guide: {style_guide_name}"}],
    ) as stream:
        return stream.get_final_text()
```

### Pattern 8: bookforge new Command

The `new` command does five things in order:
1. Create `books/<slug>/` directory tree (images/, dist/, publish/)
2. Copy default style guide to `books/<slug>/` reference (or accept `--style-guide` path)
3. Call Claude to generate story draft → write `books/<slug>/story.md`
4. Write initial `books/<slug>/state.json` (all stages pending)
5. Print next steps to terminal

```python
# bookforge/cli/new.py
import typer
from pathlib import Path
from bookforge.story.generator import generate_story
from bookforge.state import save_state

def new_command(
    slug: str = typer.Argument(..., help="Book slug, e.g. 'dangun-story'"),
    prompt: str = typer.Option(..., "--prompt", "-p", help="One-line book idea"),
    style_guide: str = typer.Option("korean-cute-watercolor", "--style", "-s"),
    pages: int = typer.Option(12, "--pages"),
):
    book_dir = Path("books") / slug
    if book_dir.exists():
        typer.echo(f"Error: {book_dir} already exists.", err=True)
        raise typer.Exit(1)

    # Create directory tree
    for subdir in ["images", "dist", "publish"]:
        (book_dir / subdir).mkdir(parents=True)

    # Generate story via Claude
    typer.echo(f"Generating story for: {prompt}")
    story_content = generate_story(prompt, style_guide, page_count=pages)
    (book_dir / "story.md").write_text(story_content)

    # Write initial state
    save_state(book_dir, {
        "version": 1,
        "slug": slug,
        "style_guide": style_guide,
        "stages": {
            "story": "complete",
            "illustrate": "pending",
            "build_en": "pending",
            "build_ko": "pending",
            "build_bilingual": "pending",
            "publish": "pending",
        },
        "pages": {},
    })

    typer.echo(f"Created: {book_dir}/")
    typer.echo(f"  story.md — review and edit before illustrating")
    typer.echo(f"Next: uv run bookforge illustrate {slug}")
```

### Anti-Patterns to Avoid

- **Business logic in CLI functions:** All story parsing, generation, validation lives in `bookforge/story/`. CLI only calls services and formats output.
- **State in memory:** Each command reads `state.json` on startup. No globals.
- **PyYAML for style guides:** `yaml.dump()` strips all comments. Use `ruamel.yaml`.
- **Hardcoding model name in code:** Model name goes in config (`BOOKFORGE_MODEL` env var or config default). `claude-sonnet-4-5` is the default, `claude-opus-4-5` is the `--quality` flag override.
- **Synchronous Anthropic call without streaming:** Stories are 2000-4000 tokens. Non-streaming `create()` will appear to hang. Always use `stream()`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML frontmatter parsing | Custom `---` splitter + yaml.safe_load | `python-frontmatter` | Edge cases: strings that contain `---`, multiline values, nested dicts, Unicode in YAML keys |
| YAML comment preservation | Manual comment re-insertion | `ruamel.yaml` CommentedMap | Round-trip loading is ruamel's entire purpose; manual is fragile |
| CLI argument parsing | argparse / sys.argv | Typer | Typer generates `--help`, handles type coercion, subcommand routing |
| Pydantic model from dict | Manual dict key checking | `Model(**dict)` + Pydantic validators | Pydantic gives field-name errors, type coercion, Optional handling |
| Atomic file write | `open(path, 'w').write()` | `write(tmp); os.replace(tmp, target)` | Direct write is non-atomic; crash mid-write corrupts state.json |

**Key insight:** The story format uses four distinct text regions per page (EN prose, KO prose, image prompt, optional image override), all embedded in a single markdown section using HTML comments. Hand-rolling a robust parser for this is a day's work. The combination of `python-frontmatter` (for YAML header) + stdlib `re` (for the body) is the right split — don't try to use a full markdown parser.

---

## Common Pitfalls

### Pitfall 1: Story Parser Discards EN Text That Contains HTML-like Strings

**What goes wrong:** The `_extract_en()` function strips ALL `<!-- ... -->` patterns to isolate English prose. But if a story page's English text contains a comparison like "she looked like a `<bear>`" or an explanation like "the symbol <!--天--> means...", the regex strips that content too.

**Why it happens:** Stripping all HTML comments is a blunt instrument.

**How to avoid:** After stripping known structured comments (`<!-- ko -->`, `<!-- /ko -->`, `<!-- image: -->`, `<!-- image-override: -->`), strip only those — not all HTML comments. The `_extract_en` function should use targeted removal, not blanket `re.sub(r'<!--.*?-->', ...)`.

**Warning signs:** English text is suspiciously short or cuts off mid-sentence.

### Pitfall 2: ruamel.yaml Requires CommentedMap — Not a Plain dict

**What goes wrong:** Writing `ruamel_yaml.dump(pydantic_model.model_dump(), stream)` loses comments because `model_dump()` returns a plain Python dict, not a `CommentedMap`. ruamel preserves comments only on its own round-tripped objects.

**How to avoid:** For reading: use ruamel to load → validate with Pydantic (read-only). For writing scaffolded style guides: write the YAML template as a literal string from code (embedded template), not by serializing a Pydantic model. Never round-trip a Pydantic model through ruamel.

### Pitfall 3: Typer Version 0.24.x Entry Point Change

**What goes wrong:** Typer 0.12+ changed how `typer.run()` vs `typer.Typer()` work for multi-command apps. Older tutorials show `@app.command()` on a single function — for a multi-subcommand app (`new`, `illustrate`, `build`, etc.), the pattern is `Typer()` with `app.command("name")(function)`.

**Note:** Typer 0.24.0 is already installed in the project environment. This version works correctly with the multi-command pattern shown above.

**How to avoid:** Always use `typer.Typer()` app with explicit `app.command("subcommand-name")(fn)` registration. Never use `typer.run(fn)` for multi-command apps.

### Pitfall 4: Claude Generation Fails Silently on Bad API Key

**What goes wrong:** `anthropic.Anthropic()` instantiates successfully even with no API key. The error only surfaces when `.stream()` is called. With no feedback, user thinks the command hung.

**How to avoid:** In `config.py`, check for `ANTHROPIC_API_KEY` at import time and print a clear error with `typer.echo(..., err=True); raise typer.Exit(1)` if missing. Don't wait for the API call to fail.

### Pitfall 5: Pydantic v2 Model Serialization Breaks ruamel Round-Trip

**What goes wrong:** `StyleGuide.model_dump()` returns native Python types. When passed to `ruamel.yaml.dump()`, the output is valid YAML but all comments are gone and dict ordering may change.

**How to avoid:** Keep Pydantic models for validation only. The canonical YAML style guide template is a hardcoded string in `bookforge/style/templates/`. Load with ruamel → validate with Pydantic → never write back via Pydantic.

---

## Code Examples

### Loading a Style Guide

```python
# bookforge/style/loader.py
from pathlib import Path
from ruamel.yaml import YAML
from bookforge.style.schema import StyleGuide

def load_style_guide(path: Path) -> StyleGuide:
    yaml = YAML()
    yaml.preserve_quotes = True
    with open(path) as f:
        data = yaml.load(f)
    # Convert ruamel CommentedMap to plain dict for Pydantic
    import json
    plain = json.loads(json.dumps(dict(data)))
    return StyleGuide(**plain)
```

### Testing the Parser with POC Data

```python
# tests/test_story_parser.py
import pytest
from pathlib import Path
from bookforge.story.parser import parse_story

SAMPLE_STORY = """\
---
title: "Test Story"
title_ko: "테스트 이야기"
slug: test-story
trim_size: "8.5x8.5"
price: 4.99
ages: "4-8"
style_guide: korean-cute-watercolor
---

## Page 1

Once upon a time.

<!-- ko -->
옛날 옛날에.
<!-- /ko -->

<!-- image: A misty mountain at dawn -->
"""

def test_parse_story(tmp_path):
    story_file = tmp_path / "story.md"
    story_file.write_text(SAMPLE_STORY)
    book = parse_story(story_file)

    assert book.meta.slug == "test-story"
    assert len(book.pages) == 1
    assert book.pages[0].text.en == "Once upon a time."
    assert book.pages[0].text.ko == "옛날 옛날에."
    assert "misty mountain" in book.pages[0].image_prompt
```

### pyproject.toml Structure

```toml
[project]
name = "bookforge"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "typer>=0.24.1",
    "rich>=14.3.3",
    "anthropic>=0.86.0",
    "python-frontmatter>=1.1.0",
    "ruamel.yaml>=0.19.1",
    "pydantic>=2.12.5",
]

[project.scripts]
bookforge = "bookforge.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[dependency-groups]
dev = [
    "pytest",
    "pytest-asyncio",
    "respx",
]
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| argparse for CLI | Typer with type hints | ~2020 (Typer 0.1) | Zero boilerplate argument definition; auto `--help` |
| PyYAML for all YAML | ruamel.yaml for human-edited YAML | Ongoing best practice | Comments survive round-trips; critical for config files |
| Pydantic v1 `@validator` | Pydantic v2 `@field_validator` | Pydantic 2.0 (2023) | Different decorator; v2 validators are class methods |
| `anthropic.Client` (old) | `anthropic.Anthropic()` (current) | SDK 0.20+ | Updated constructor; streaming via `.stream()` context manager |

**Deprecated/outdated:**
- `pydantic.validator` decorator: replaced by `@field_validator` in Pydantic v2. Any tutorial using `@validator` is v1 and wrong for this project.
- `typer.run(fn)`: for single-function CLIs only. Multi-command apps must use `typer.Typer()`.
- `anthropic.Client(api_key=...)`: replaced by `anthropic.Anthropic()` which reads env var automatically.

---

## Open Questions

1. **Exact story.md format: `## Page N` vs `<!-- page:N -->`**
   - What we know: REQUIREMENTS.md says `## Page N` (STOR-02). ARCHITECTURE.md draft shows `<!-- page:01 -->` syntax.
   - What's unclear: Minor discrepancy between two planning docs.
   - Recommendation: REQUIREMENTS.md is authoritative. Use `## Page N` headers. The parser regex is `re.split(r'^## Page \d+', content, flags=re.MULTILINE)`.

2. **Where does STYL-03 character sheet generation live in Phase 1?**
   - What we know: STYL-03 says "Ho-rang and Gom-i character sheets generated upfront as reference images." Phase 1 includes STYL-03 per REQUIREMENTS.md traceability table.
   - What's unclear: Actual image generation requires the Replicate/image provider (Phase 2 scope).
   - Recommendation: Phase 1 scope for STYL-03 = define `CharacterDef` models + scaffold placeholder PNG paths in style guide + write to state.json. The actual generation of reference images is triggered in Phase 2 as the first step before any page generation.

3. **`bookforge new` — should story generation be synchronous or stream to terminal?**
   - What we know: Stories are 2000-4000 tokens; streaming is strongly preferred for UX.
   - Recommendation: Use `client.messages.stream()` context manager and stream output to terminal with `typer.echo()` per chunk, then write the complete text to story.md. User sees progress.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (current stable) + pytest-asyncio |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` — Wave 0 |
| Quick run command | `uv run pytest tests/ -x -q` |
| Full suite command | `uv run pytest tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CLI-01 | `bookforge new <slug>` creates directory tree + state.json | integration | `uv run pytest tests/test_new_command.py -x` | Wave 0 |
| STOR-01 | YAML frontmatter parsed into BookMeta | unit | `uv run pytest tests/test_story_parser.py::test_frontmatter -x` | Wave 0 |
| STOR-02 | `## Page N` headers split story into pages | unit | `uv run pytest tests/test_story_parser.py::test_page_splitting -x` | Wave 0 |
| STOR-03 | Korean text extracted from `<!-- ko -->` blocks | unit | `uv run pytest tests/test_story_parser.py::test_ko_extraction -x` | Wave 0 |
| STOR-04 | Image prompts extracted from `<!-- image: -->` | unit | `uv run pytest tests/test_story_parser.py::test_image_prompt -x` | Wave 0 |
| STOR-05 | Claude API called + story.md written | integration (mocked) | `uv run pytest tests/test_generator.py -x` | Wave 0 |
| STOR-06 | `image-override` read as `Page.image_override` | unit | `uv run pytest tests/test_story_parser.py::test_image_override -x` | Wave 0 |
| STYL-01 | Style guide YAML loads into StyleGuide model | unit | `uv run pytest tests/test_style_loader.py::test_load -x` | Wave 0 |
| STYL-02 | Character definitions load into CharacterDef | unit | `uv run pytest tests/test_style_loader.py::test_characters -x` | Wave 0 |
| STYL-03 | CharacterDef has reference_image path | unit | `uv run pytest tests/test_style_loader.py::test_ref_image -x` | Wave 0 |
| STYL-04 | `build_prompt_prefix()` returns assembled string | unit | `uv run pytest tests/test_style_loader.py::test_prompt_prefix -x` | Wave 0 |
| STYL-05 | image.provider field present and validated | unit | `uv run pytest tests/test_style_loader.py::test_provider -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/ -x -q`
- **Per wave merge:** `uv run pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

All test files need to be created — no test infrastructure exists yet:

- [ ] `tests/conftest.py` — shared fixtures (sample story.md, sample style guide YAML, tmp book dir)
- [ ] `tests/test_story_parser.py` — covers STOR-01 through STOR-06
- [ ] `tests/test_style_loader.py` — covers STYL-01 through STYL-05
- [ ] `tests/test_state.py` — atomic write/read, state schema
- [ ] `tests/test_new_command.py` — covers CLI-01 (uses Typer test client + mocked Claude)
- [ ] `tests/test_generator.py` — covers STOR-05 (mocked with respx)
- [ ] `pyproject.toml` — does not exist yet; must be created in Wave 0

---

## Sources

### Primary (HIGH confidence)

- PyPI `typer 0.24.0` — confirmed installed in project environment
- PyPI `pydantic 2.12.5` — confirmed installed in project environment
- [Typer docs — Commands and Groups](https://typer.tiangolo.com/tutorial/commands/one-or-multiple/) — multi-command app pattern
- [python-frontmatter PyPI](https://pypi.org/project/python-frontmatter/) — `frontmatter.load()` API
- [ruamel.yaml docs](https://yaml.readthedocs.io/en/latest/) — CommentedMap round-trip behavior
- [Pydantic v2 validators](https://docs.pydantic.dev/latest/concepts/validators/) — `@field_validator` syntax
- [Anthropic Python SDK streaming](https://github.com/anthropics/anthropic-sdk-python#streaming) — `.stream()` context manager

### Secondary (MEDIUM confidence)

- ARCHITECTURE.md (project planning doc) — component boundaries, data flow, directory structure
- STACK.md (project planning doc) — library versions, installation commands

### Tertiary (LOW confidence)

- None — all findings have primary or secondary verification for Phase 1 scope.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions verified against installed environment and prior PyPI research
- Architecture: HIGH — directly derived from project's own ARCHITECTURE.md and REQUIREMENTS.md
- Pitfalls: HIGH for parser edge cases (re-verified against known Python regex behavior); MEDIUM for ruamel/Pydantic interaction (documented pattern, not tested yet)

**Research date:** 2026-03-24
**Valid until:** 2026-06-24 (stable libraries; 90 days)
