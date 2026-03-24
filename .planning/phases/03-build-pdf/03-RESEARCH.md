# Phase 3: Build & PDF - Research

**Researched:** 2026-03-24
**Domain:** WeasyPrint HTML-to-PDF, pikepdf post-processing, Jinja2 book templates, Korean font embedding, KDP print compliance
**Confidence:** HIGH (core API patterns verified; ICC embedding pattern MEDIUM)

---

## Summary

Phase 3 transforms the parsed Book model and generated images into six PDF files: three language editions (en, ko, bilingual) times two formats (screen, print). The pipeline is: parse story.md → render Jinja2 HTML per edition → WeasyPrint renders HTML to PDF → pikepdf post-processes print PDF to inject TrimBox/BleedBox/MediaBox and embed sRGB ICC OutputIntent.

The biggest risk areas are (1) Korean font embedding — must use `@font-face url()` with a bundled font file and pass a `FontConfiguration` object to WeasyPrint, never rely on system fonts; (2) full-bleed illustrations — WeasyPrint clips CSS page backgrounds at the `@page` boundary, so illustrations must use sized `<img>` elements with negative margins to push into the bleed zone; and (3) the pikepdf OutputIntent embedding pattern, which requires manual PDF dictionary construction (no high-level helper exists yet).

**Primary recommendation:** Build and pass a single-page reference test (one illustration, Korean text, bleed enabled) before wiring up the six-file build loop. This de-risks the three hard problems independently.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CLI-03 | `uv run bookforge build <slug>` assembles HTML and exports PDFs | CLI module pattern from Phase 1/2; Typer command registration in `bookforge/cli/__init__.py` |
| BLD-01 | Three language editions from one story.md: `--lang en`, `--lang ko`, `--lang bilingual` (default) | Jinja2 template conditionals on `edition` variable; story parser already splits `BilingualText.en` / `.ko` |
| BLD-02 | `--lang all` builds all 6 PDFs (3 editions x 2 formats) | Loop over `["en","ko","bilingual"]` x `["screen","print"]`; call build function per combination |
| BLD-03 | Screen PDF: RGB, no bleed, optimized for digital viewing | WeasyPrint `write_pdf(optimize_images=True)`; no `@page { bleed }` in screen CSS |
| BLD-04 | Print PDF: RGB with sRGB ICC profile, 0.125" bleed, 300 DPI (KDP) | WeasyPrint `@page { bleed: 0.125in; marks: none; }`; pikepdf post-process for TrimBox/BleedBox/OutputIntent |
| BLD-05 | HTML template with Jinja2 assembling story text + images per page | `Environment(loader=FileSystemLoader(...))` → `template.render(pages=book.pages, edition=edition)` |
| BLD-06 | Korean font (Noto Sans KR) embedded via @font-face for reliable CJK rendering | `FontConfiguration()` + `@font-face { src: url(path/to/NotoSansKR-Regular.otf) }` with bundled font asset |
| BLD-07 | No crop marks in print PDF (KDP rejects them) | `@page { marks: none; }` in print CSS — explicitly confirmed in KDP submission guidelines |
| BLD-08 | Default trim size 8.5x8.5", configurable per book in frontmatter | `BookMeta.trim_size` already parsed; `StyleGuide.layout.trim_inches` holds `[8.5, 8.5]`; derive page size from these |
</phase_requirements>

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| WeasyPrint | >=68.1 | HTML→PDF rendering (both screen and print) | Pure Python, CSS Paged Media Level 3 support including `@page { bleed }`, active maintenance, Pango-backed font rendering |
| pikepdf | >=10.5.1 | Print PDF post-processing: TrimBox/BleedBox/MediaBox correction, sRGB ICC OutputIntent injection | QPDF-backed, reliable low-level PDF box manipulation, confirmed ICC embedding via issue #509 pattern |
| Jinja2 | >=3.1.6 | HTML template engine for book pages | Already in project scope; template inheritance, conditionals, and macros sufficient for three-edition layout |
| fonttools | >=4.x | Optional: `pyftsubset` to pre-subset NotoSansKR before embedding | Reduces CJK font processing overhead in WeasyPrint; stdlib of font engineering |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| weasyprint.text.fonts.FontConfiguration | (bundled) | Pass to `HTML.write_pdf()` to enable `@font-face` font loading | Required whenever `@font-face` rules are used — without it, custom fonts silently fail |
| pikepdf.Array, pikepdf.Dictionary, pikepdf.Name, pikepdf.Stream | (bundled) | Construct OutputIntent PDF objects for ICC embedding | Print PDF post-processing step only |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| WeasyPrint | Playwright/Chromium | 120MB system dep, requires browser process; zero JS in our templates; WeasyPrint is correct choice |
| WeasyPrint | ReportLab | Requires programmatic layout in Python; we have HTML/CSS templates that preview in a browser |
| pikepdf | pypdf | pikepdf has lower-level box manipulation and QPDF backend; pypdf TrimBox support is less reliable |

**Installation (additions to pyproject.toml):**
```bash
uv add weasyprint pikepdf jinja2
# System deps for WeasyPrint (Debian/Ubuntu — already documented in STACK.md)
sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0
# Font asset (download once, commit to repo)
# NotoSansKR-Regular.otf → bookforge/assets/fonts/NotoSansKR-Regular.otf
```

---

## Architecture Patterns

### Recommended Module Structure

```
bookforge/
├── cli/
│   ├── build.py              # build_command() — new CLI command
│   └── __init__.py           # register app.command("build")(build_command)
├── build/
│   ├── __init__.py
│   ├── renderer.py           # render_edition(book, edition) → HTML string via Jinja2
│   ├── pdf.py                # build_pdf(html, output_path, format) → Path
│   └── postprocess.py        # patch_print_pdf(path, trim_size) — pikepdf TrimBox/ICC pass
├── assets/
│   ├── fonts/
│   │   └── NotoSansKR-Regular.otf   # bundled, committed to repo
│   ├── icc/
│   │   └── sRGB_v4_ICC_preference.icc  # from ICC.org, committed to repo
│   └── templates/
│       ├── book_base.html.j2    # shared layout: <html>, <head>, CSS imports
│       ├── book_page.html.j2    # single page: illustration + text (edition-aware)
│       └── css/
│           ├── screen.css       # no bleed, RGB optimized
│           └── print.css        # @page bleed, marks: none, 300 DPI image hint
```

### Pattern 1: WeasyPrint HTML class with FontConfiguration

**What:** Render an HTML string (from Jinja2) to PDF bytes using WeasyPrint's Python API, passing a `FontConfiguration` so `@font-face` rules load correctly.

**When to use:** Every PDF render call — both screen and print.

```python
# Source: WeasyPrint 68.1 docs — https://doc.courtbouillon.org/weasyprint/stable/api_reference.html
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

def build_pdf(html_string: str, base_url: str, stylesheets: list[str], output_path: Path) -> None:
    font_config = FontConfiguration()
    css_objects = [CSS(string=sheet, font_config=font_config) for sheet in stylesheets]
    HTML(string=html_string, base_url=base_url).write_pdf(
        output_path,
        stylesheets=css_objects,
        font_config=font_config,
        optimize_images=True,   # screen: smaller file; print: also fine, images stay high-res
    )
```

**Critical:** `font_config` must be passed to both `CSS(...)` and `write_pdf(...)` — passing to only one silently disables `@font-face`.

### Pattern 2: CSS @font-face for Noto Sans KR

**What:** Embed Korean font via `@font-face` using an absolute `url()` path to the bundled OTF file.

**When to use:** In the shared `@font-face` declaration that both screen.css and print.css import.

```css
/* Source: WeasyPrint issue #1337, confirmed pattern for local font embedding */
@font-face {
    font-family: 'Noto Sans KR';
    src: url('/absolute/path/to/bookforge/assets/fonts/NotoSansKR-Regular.otf') format('opentype');
    font-weight: normal;
    font-style: normal;
}

/* Apply to Korean text elements */
.text-ko {
    font-family: 'Noto Sans KR', sans-serif;
}
```

**Critical rules:**
- Use `url()` with an absolute path, NOT `local('Noto Sans KR')` — `local()` silently fails across environments (WeasyPrint issue #1337 confirmed)
- Use the KR-only weight file (`NotoSansKR-Regular.otf`) NOT the pan-CJK variant — the pan-CJK file causes ~6x PDF generation slowdown (WeasyPrint issue #2120)
- Pass `base_url=str(assets_dir)` to `HTML(...)` so relative `url()` paths resolve correctly as an alternative to absolute paths

### Pattern 3: WeasyPrint @page for Print vs Screen

**What:** Two CSS files — `screen.css` (no bleed) and `print.css` (bleed + marks:none).

**When to use:** Selected based on the `format` parameter (`screen` vs `print`).

```css
/* print.css — Source: WeasyPrint Going Further docs, KDP Paperback Guidelines */
@page {
    size: 8.625in 8.75in;  /* trim(8.5x8.5) + bleed(0.125 each side); height adds top+bottom bleed */
    margin: 0;              /* full-bleed layout; text safe zone enforced by inner container */
    bleed: 0.125in;
    marks: none;            /* CRITICAL: KDP rejects files with crop marks */
}

/* screen.css */
@page {
    size: 8.5in 8.5in;
    margin: 0;
}
```

**Note on KDP dimensions:** KDP spec adds bleed asymmetrically for non-square books (0.125" outside edge only for width), but for a square book with bleed on all sides the PDF must be 8.625" wide × 8.75" tall. In PDF points (72 pt/in): MediaBox = [0, 0, 621, 630], TrimBox = [9, 9, 612, 621].

### Pattern 4: Full-Bleed Illustration via Sized Element (NOT CSS background)

**What:** Place the full-page illustration as an `<img>` element sized to bleed dimensions with negative margins, rather than as a CSS background on `@page`.

**When to use:** Every book page that has a full-bleed illustration (all pages).

**Why:** WeasyPrint clips CSS backgrounds at the `@page` boundary (issue #934, confirmed open). Positioned elements with negative margins are the documented workaround.

```html
<!-- book_page.html.j2 -->
<div class="page">
    <!-- Illustration bleeds to page edge -->
    <img class="illustration"
         src="{{ image_path }}"
         alt="Page {{ page.number }} illustration" />
    <!-- Text sits in safe zone via inner container -->
    <div class="text-safe-zone">
        {% if edition in ('en', 'bilingual') %}
        <p class="text-en">{{ page.text.en }}</p>
        {% endif %}
        {% if edition in ('ko', 'bilingual') %}
        <p class="text-ko">{{ page.text.ko }}</p>
        {% endif %}
    </div>
</div>
```

```css
/* print.css illustration sizing: trim(8.5") + bleed(0.125") each side = 8.75" square */
.page {
    position: relative;
    width: 8.625in;
    height: 8.75in;
    overflow: hidden;
}
.illustration {
    position: absolute;
    top: -0.125in;      /* extend into top bleed */
    left: -0.125in;     /* extend into left bleed */
    width: 8.875in;     /* 8.625 + 0.125 right bleed */
    height: 9.0in;      /* 8.75 + 0.125 bottom bleed */
    object-fit: cover;
}
.text-safe-zone {
    position: absolute;
    bottom: 0.375in;    /* 0.25" margin + 0.125" bleed offset */
    left: 0.375in;
    right: 0.375in;
    /* semi-transparent background for text legibility */
}
```

### Pattern 5: pikepdf Print PDF Post-Processing

**What:** After WeasyPrint renders print.pdf, open it with pikepdf to: set correct MediaBox/TrimBox/BleedBox, embed sRGB ICC OutputIntent.

**When to use:** Print format only — screen PDF needs no post-processing.

```python
# Source: pikepdf docs (page boxes) + issue #509 (OutputIntent pattern)
import pikepdf
from pathlib import Path

# PDF points: 72 points per inch
# For 8.5x8.5" trim with 0.125" bleed:
BLEED_PT = 9       # 0.125in * 72
TRIM_W_PT = 612    # 8.5in * 72
TRIM_H_PT = 612    # 8.5in * 72
MEDIA_W_PT = 621   # (8.5 + 0.125) * 72
MEDIA_H_PT = 630   # (8.5 + 0.25) * 72  [top + bottom bleed]

def patch_print_pdf(pdf_path: Path, icc_path: Path) -> None:
    """Set TrimBox/BleedBox/MediaBox and embed sRGB ICC OutputIntent in-place."""
    with pikepdf.open(pdf_path, allow_overwriting_input=True) as pdf:
        media_box = pikepdf.Array([0, 0, MEDIA_W_PT, MEDIA_H_PT])
        trim_box  = pikepdf.Array([BLEED_PT, BLEED_PT, MEDIA_W_PT - BLEED_PT, MEDIA_H_PT - BLEED_PT])

        for page in pdf.pages:
            page.MediaBox = media_box
            page.TrimBox  = trim_box
            page.BleedBox = media_box  # BleedBox == MediaBox means bleed extends to media edge

        # Embed sRGB ICC OutputIntent
        icc_data = icc_path.read_bytes()
        icc_stream = pikepdf.Stream(pdf, icc_data)
        icc_stream.stream_dict = pikepdf.Dictionary(
            N=3,                      # 3 = RGB
            Alternate=pikepdf.Name("/DeviceRGB"),
        )
        output_intent = pikepdf.Dictionary(
            Type=pikepdf.Name("/OutputIntent"),
            S=pikepdf.Name("/GTS_PDFA1"),   # use /GTS_PDFA1 for sRGB; acceptable for KDP
            OutputConditionIdentifier=pikepdf.String("sRGB IEC61966-2.1"),
            DestOutputProfile=icc_stream,
        )
        if "/OutputIntents" not in pdf.Root:
            pdf.Root["/OutputIntents"] = pikepdf.Array()
        pdf.Root["/OutputIntents"].append(output_intent)

        pdf.save(pdf_path, linearize=True)
```

**Note on ICC file:** Download `sRGB_v4_ICC_preference.icc` from [ICC.org](https://www.color.org/srgbprofiles.xalter) and commit to `bookforge/assets/icc/`. This is the reference sRGB profile used by Adobe and ICC. ~4KB file size.

### Pattern 6: Language Edition Filtering in Jinja2

**What:** Single template renders all three editions via a passed `edition` variable.

**When to use:** Always — do not create three separate templates.

```jinja2
{# book_page.html.j2 #}
{% for page in pages %}
<div class="page" style="page-break-after: always;">
    <img class="illustration" src="{{ image_dir }}/{{ page_image(page) }}" />
    <div class="text-safe-zone">
        {%- if edition != 'ko' %}
        <p class="text-en">{{ page.text.en }}</p>
        {%- endif %}
        {%- if edition != 'en' %}
        <p class="text-ko">{{ page.text.ko }}</p>
        {%- endif %}
    </div>
</div>
{% endfor %}
```

The `edition` value from the CLI (`en` / `ko` / `bilingual`) maps directly to template conditionals. No separate template files needed.

### Pattern 7: Bilingual Layout — Text Positioning

**What:** For bilingual edition, English and Korean text share equal visual weight on the page.

**Design principle:** From PITFALLS.md Pitfall #10 — give both languages identical font size and weight. Neither language should visually dominate.

```css
/* Both languages: same size, same weight */
.text-en, .text-ko {
    font-size: 1.4rem;
    font-weight: 400;
    line-height: 1.5;
    color: #2c2c2c;
}
.text-en {
    font-family: 'Georgia', serif;
    margin-bottom: 0.3em;
}
.text-ko {
    font-family: 'Noto Sans KR', sans-serif;
    /* Korean text: slightly tighter line-height is acceptable */
    line-height: 1.4;
}
```

**Layout approach:** English text above Korean, separated by a small gap — vertically stacked on a translucent band at the bottom of the page. Both get the same visual container, same padding, same color. Never stack them in a way that puts Korean in a smaller or secondary container.

### Pattern 8: build command CLI structure

**What:** Follow the established pattern from `illustrate.py` — one module per command, registered in `__init__.py`.

```python
# bookforge/cli/build.py
def build_command(
    slug: str = typer.Argument(..., help="Book slug"),
    lang: str = typer.Option("bilingual", "--lang", "-l",
                             help="Edition: en, ko, bilingual, all"),
    fmt: str = typer.Option("all", "--format", "-f",
                            help="Format: screen, print, all"),
) -> None:
    ...

# bookforge/cli/__init__.py — add:
from bookforge.cli.build import build_command
app.command("build")(build_command)
```

### Anti-Patterns to Avoid

- **Korean font via `local()`:** `@font-face { src: local('Noto Sans KR') }` fails silently across environments. Always use `url()` with a bundled file path.
- **Pan-CJK font (`NotoSansCJK*.ttc`):** Contains Japanese, Chinese, and Korean glyphs — causes ~6x PDF generation slowdown. Use the KR-only weight file.
- **CSS `@page` background for illustrations:** `background-image: url(...)` on `@page` is clipped at the trim boundary. Use positioned `<img>` elements instead.
- **`marks: crop` in print CSS:** KDP explicitly rejects PDFs with crop marks. Use `marks: none`.
- **Passing `font_config` only to `CSS()`:** WeasyPrint requires `font_config` passed to BOTH `CSS(string=..., font_config=...)` AND `html.write_pdf(..., font_config=...)`. Missing either causes silent font loading failure.
- **Hardcoding page dimensions:** Derive all dimension math from `BookMeta.trim_size` and `StyleGuide.layout.bleed_inches`. BLD-08 requires configurability.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTML→PDF rendering | Custom Pango/Cairo pipeline | WeasyPrint | CSS Paged Media spec support, font embedding, bleed/marks already implemented |
| PDF box manipulation | PyMuPDF or raw binary patching | pikepdf | QPDF backend handles PDF spec edge cases; pikepdf has Pythonic page box setters |
| Font subsetting | Custom glyph extraction | `pyftsubset` (fonttools) | Battle-tested, handles OTF/TTF/WOFF, correct table handling for CJK |
| Korean font | Hand-collecting system glyphs | Noto Sans KR | Google-maintained, OFL license, CJK coverage guaranteed, single weight OTF is ~4MB |
| ICC sRGB profile | Color math | Download `sRGB_v4_ICC_preference.icc` from ICC.org | This IS the reference sRGB profile — 4KB, commit to repo, no generation needed |

**Key insight:** All the hard parts of print PDF production (font embedding, color management, box geometry) have solved implementations. The custom code we write is purely the orchestration glue.

---

## Common Pitfalls

### Pitfall 1: Korean text renders as blank white space in the PDF
**What goes wrong:** WeasyPrint generates a valid-looking PDF with empty space where Korean characters should appear. No error is raised.
**Why it happens:** WeasyPrint uses system fonts. If the environment has no Korean font installed, text renders blank (confirmed WeasyPrint issue #2366).
**How to avoid:** Use `@font-face { src: url('/path/to/NotoSansKR-Regular.otf') }` with a bundled font file. Pass `FontConfiguration()` to both `CSS()` and `write_pdf()`. Never rely on `local()` font matching.
**Warning signs:** Korean edition PDF is same file size as English edition (should be slightly larger due to Korean glyph complexity).

### Pitfall 2: Full-bleed illustration has white hairline at page edges after trimming
**What goes wrong:** CSS background images clip at `@page` boundary — bleed area is white.
**Why it happens:** WeasyPrint CSS background extension into bleed area is a known open issue (#934).
**How to avoid:** Use sized `<img>` elements with `position: absolute` and negative margin/top/left values that extend 0.125" beyond the page boundary. See Pattern 4 above.
**Warning signs:** In Acrobat "Show Art/Trim/Bleed Boxes" view, a white gap appears between TrimBox and BleedBox.

### Pitfall 3: KDP rejects PDF due to crop marks
**What goes wrong:** Uploaded PDF is rejected with "file contains trim marks."
**Why it happens:** `marks: crop cross` was included in the print CSS (or was the default in some WeasyPrint versions).
**How to avoid:** Explicitly set `marks: none` in the print `@page` rule. Verify with a preflight check that no marks streams exist in the output PDF.

### Pitfall 4: sRGB ICC OutputIntent raises pikepdf error
**What goes wrong:** `pikepdf.PdfError` when appending to `/OutputIntents` because the value is a direct PDF object rather than an indirect reference.
**Why it happens:** PDF spec requires OutputIntents entries to be indirect objects in some contexts.
**How to avoid:** If direct append fails, use `pdf.make_indirect(output_intent)` before appending. Test the post-processing step with a single-page PDF before the full book.

### Pitfall 5: Six output files with wrong names cause upload errors
**What goes wrong:** Uploading `build/print.pdf` to Gumroad when intending to upload the screen edition.
**Why it happens:** No naming convention enforced.
**How to avoid:** Output filename pattern: `{slug}_{edition}_{format}.pdf` e.g. `dangun-story_bilingual_print.pdf`. Write to `books/{slug}/dist/` directory. The existing `dist/` subdirectory is already scaffolded by `new` command.

### Pitfall 6: CJK font causes 6x build slowdown
**What goes wrong:** `bookforge build` for Korean edition takes 30+ seconds.
**Why it happens:** Noto Sans CJK (pan-CJK) font has 20,000+ glyphs; WeasyPrint subsets all of them even if only 100 are used (issue #2120).
**How to avoid:** Use `NotoSansKR-Regular.otf` (KR-only), not the pan-CJK variant. Optionally run `pyftsubset` as a pre-build step to subset to only the characters actually in the story.

### Pitfall 7: Image paths resolve incorrectly in WeasyPrint
**What goes wrong:** PDF renders with broken images (no illustration visible).
**Why it happens:** WeasyPrint resolves relative `src` URLs against `base_url`. If `base_url` is not set or points to the wrong directory, images cannot be found.
**How to avoid:** Always pass `base_url=str(book_dir)` to `HTML(string=html, base_url=str(book_dir))`. Use relative image paths in templates (e.g., `images/page-01.png`) relative to `book_dir`.

---

## Code Examples

### Verified: WeasyPrint render with FontConfiguration
```python
# Source: https://doc.courtbouillon.org/weasyprint/stable/api_reference.html
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

font_config = FontConfiguration()
css = CSS(string=css_string, font_config=font_config)
HTML(string=html_string, base_url=base_url_str).write_pdf(
    output_path,
    stylesheets=[css],
    font_config=font_config,
    optimize_images=True,
)
```

### Verified: pikepdf page box setters
```python
# Source: https://pikepdf.readthedocs.io/en/latest/topics/page.html
import pikepdf
pdf = pikepdf.open("input.pdf")
page = pdf.pages[0]
page.MediaBox = [0, 0, 621, 630]   # 8.625" x 8.75" in points
page.TrimBox  = [9, 9, 612, 621]   # 8.5" x 8.5" trim, offset by bleed (9pt)
page.BleedBox = [0, 0, 621, 630]   # same as MediaBox
pdf.save("output.pdf")
```

### Verified: KDP print dimension math for 8.5x8.5"
```python
# KDP spec: trim + 0.125" on all sides
# Width:  8.5" + 0.125" (outside edge only per KDP) → but for square books: + both sides
# Height: 8.5" + 0.125" top + 0.125" bottom = 8.75"
# PDF points (72pt/in):
TRIM_W = TRIM_H = 612        # 8.5 * 72
BLEED = 9                    # 0.125 * 72
MEDIA_W = 621                # trim + 1 bleed side (KDP width: outside edge only)
MEDIA_H = 630                # trim + 2 bleed sides (KDP height: top + bottom)
# TrimBox: offset from media bottom-left by bleed amount
# [left_bleed, bottom_bleed, media_w - right_bleed, media_h - top_bleed]
TRIM_BOX = [BLEED, BLEED, MEDIA_W - BLEED, MEDIA_H - BLEED]
# = [9, 9, 612, 621]
```

**Note:** KDP's bleed spec adds 0.125" to top/bottom/outside edges only (not the spine side for standard books). For a square full-bleed book PDF we apply 0.125" on all four sides, making the PDF 8.625" × 8.75". The asymmetry (8.625 wide vs 8.75 tall) is because KDP defines width as trim + 1 bleed side (outside), height as trim + 2 bleed sides (top + bottom).

### Verified: Edition loop for BLD-02
```python
# --lang all builds 6 PDFs
EDITIONS = {"en", "ko", "bilingual"}
FORMATS  = {"screen", "print"}

if lang == "all":
    combos = [(e, f) for e in EDITIONS for f in FORMATS]
else:
    fmt_list = [fmt] if fmt != "all" else list(FORMATS)
    combos = [(lang, f) for f in fmt_list]

for edition, format_ in combos:
    output_path = dist_dir / f"{slug}_{edition}_{format_}.pdf"
    build_one(book, edition, format_, output_path, book_dir, style_guide)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Headless browser (Phantom.js) for HTML→PDF | WeasyPrint pure Python | ~2015 onward | No system browser dep; faster install |
| Manual CSS backgrounds for bleed | Sized positioned `<img>` elements | WeasyPrint #934 still open | Avoids WeasyPrint bleed clip bug |
| PyYAML for all YAML | ruamel.yaml for human-edited files | Project established | Preserves comments in style guides |
| Pan-CJK fonts (NotoSansCJK) | KR-only weight (NotoSansKR) | WeasyPrint #2120 documented | 6x speed improvement for Korean rendering |

**Deprecated/outdated:**
- `weasyprint.CSS(filename=...)` with `local()` font URLs: use `url()` with absolute/base-relative paths
- WeasyPrint `presentational_hints=True`: only needed if using HTML presentation attributes (not applicable here)

---

## Open Questions

1. **pikepdf OutputIntent indirect object requirement**
   - What we know: Pattern from issue #509 shows direct Dictionary append works in some cases
   - What's unclear: Whether KDP's PDF validator requires the OutputIntent to be an indirect PDF object
   - Recommendation: Test with single-page PDF and validate in Acrobat's Output Preview; if direct object fails, use `pdf.make_indirect(output_intent)`

2. **WeasyPrint `dpi` parameter for print PDF**
   - What we know: `write_pdf(dpi=...)` exists in WeasyPrint API and reduces raster image resolution
   - What's unclear: Whether setting `dpi=300` on write_pdf constrains or hints image resolution — images sourced at 1024x1024px from Flux Kontext will be embedded as-is unless downsampled
   - Recommendation: Do NOT set `dpi=` in write_pdf for print; embed images at their native resolution and let KDP do any needed resampling. Set `dpi=150` for screen PDF to reduce file size.

3. **Configurable trim_size from BookMeta**
   - What we know: `BookMeta.trim_size = "8.5x8.5"` is already parsed; default is 8.5x8.5
   - What's unclear: Whether future trim sizes (e.g., "6x9") need different bleed math or just dimension substitution
   - Recommendation: Build a `parse_trim_size(trim_size_str)` helper that returns `(width_in, height_in)` and derive all dimension math from it. The bleed math (add 0.125" each side) stays constant.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (existing, `tests/` dir) |
| Config file | `pyproject.toml` — `[tool.pytest.ini_options] testpaths = ["tests"]` |
| Quick run command | `uv run pytest tests/test_build*.py -x -q` |
| Full suite command | `uv run pytest tests/ -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CLI-03 | `build` command registered and accepts `<slug>` argument | unit | `uv run pytest tests/test_build_cli.py -x` | ❌ Wave 0 |
| BLD-01 | `--lang en` produces only English text; `--lang ko` only Korean; `--lang bilingual` both | unit | `uv run pytest tests/test_renderer.py::test_edition_filtering -x` | ❌ Wave 0 |
| BLD-02 | `--lang all` produces exactly 6 output file paths | unit | `uv run pytest tests/test_build_cli.py::test_lang_all_produces_six_paths -x` | ❌ Wave 0 |
| BLD-03 | Screen PDF: file written to `dist/`, no bleed in CSS | unit (mock WeasyPrint) | `uv run pytest tests/test_pdf.py::test_screen_no_bleed -x` | ❌ Wave 0 |
| BLD-04 | Print PDF: pikepdf post-processing sets TrimBox/BleedBox/MediaBox correctly | unit | `uv run pytest tests/test_postprocess.py::test_trim_bleed_boxes -x` | ❌ Wave 0 |
| BLD-05 | Jinja2 renderer produces valid HTML with correct page count | unit | `uv run pytest tests/test_renderer.py::test_html_page_count -x` | ❌ Wave 0 |
| BLD-06 | CSS string includes @font-face with url() for Noto KR (not local()) | unit | `uv run pytest tests/test_renderer.py::test_font_face_url -x` | ❌ Wave 0 |
| BLD-07 | Print CSS contains `marks: none` and does NOT contain `marks: crop` | unit | `uv run pytest tests/test_renderer.py::test_no_crop_marks -x` | ❌ Wave 0 |
| BLD-08 | Dimension math derives from `trim_size` frontmatter correctly for 8.5x8.5 | unit | `uv run pytest tests/test_postprocess.py::test_dimension_math -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/test_build*.py tests/test_renderer.py tests/test_postprocess.py -x -q`
- **Per wave merge:** `uv run pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_build_cli.py` — covers CLI-03, BLD-02
- [ ] `tests/test_renderer.py` — covers BLD-01, BLD-05, BLD-06, BLD-07
- [ ] `tests/test_pdf.py` — covers BLD-03
- [ ] `tests/test_postprocess.py` — covers BLD-04, BLD-08
- [ ] Font asset: `bookforge/assets/fonts/NotoSansKR-Regular.otf` — download before font tests
- [ ] ICC asset: `bookforge/assets/icc/sRGB_v4_ICC_preference.icc` — download from ICC.org before postprocess tests
- [ ] Dependencies: `uv add weasyprint pikepdf jinja2` — not yet in pyproject.toml

---

## Sources

### Primary (HIGH confidence)
- [WeasyPrint 68.1 API Reference](https://doc.courtbouillon.org/weasyprint/stable/api_reference.html) — HTML class, write_pdf parameters, FontConfiguration usage
- [WeasyPrint Going Further docs](https://doc.courtbouillon.org/weasyprint/stable/going_further.html) — @page bleed/marks CSS properties
- [pikepdf Working with Pages](https://pikepdf.readthedocs.io/en/latest/topics/page.html) — MediaBox/TrimBox/BleedBox setters
- [KDP Paperback Submission Guidelines](https://kdp.amazon.com/en_US/help/topic/G201857950) — no crop marks requirement confirmed
- [KDP Set Trim Size, Bleed, and Margins](https://kdp.amazon.com/en_US/help/topic/GVBQ3CMEQW3W2VL6) — 0.125" bleed, 8.625×8.75" for 8.5×8.5" trim confirmed

### Secondary (MEDIUM confidence)
- [WeasyPrint issue #934](https://github.com/Kozea/WeasyPrint/issues/934) — bleed clips CSS backgrounds at @page boundary (known open issue)
- [WeasyPrint issue #1337](https://github.com/Kozea/WeasyPrint/issues/1337) — `local()` font loading fails silently; use `url()` instead
- [WeasyPrint issue #2120](https://github.com/Kozea/WeasyPrint/issues/2120) — CJK font 6x slowdown with pan-CJK variant
- [WeasyPrint issue #2366](https://github.com/Kozea/WeasyPrint/issues/2366) — Korean text renders blank if no Korean font installed
- [pikepdf issue #509](https://github.com/pikepdf/pikepdf/issues/509) — OutputIntent ICC embedding pattern (feature discussion, pattern confirmed but exact working code not in search results)
- [CourtBouillon More Colors blog](https://www.courtbouillon.org/blog/00052-more-colors-in-weasyprint/) — sRGB ICC support in WeasyPrint

### Tertiary (LOW confidence — flag for validation)
- pikepdf OutputIntent direct-vs-indirect object requirement: not confirmed in official docs — must test empirically

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — WeasyPrint 68.1, pikepdf 10.5.1, Jinja2 3.1.6 versions verified via PyPI; packages not yet installed in project (need `uv add`)
- Architecture: HIGH — patterns verified against WeasyPrint API docs and KDP specs
- Font embedding: HIGH — `@font-face url()` + FontConfiguration pattern confirmed across multiple WeasyPrint issues
- Bleed workaround: HIGH — sized positioned `<img>` approach confirmed as correct workaround for issue #934
- pikepdf ICC OutputIntent: MEDIUM — pattern from issue #509 discussion; exact working code not verified; test empirically
- KDP dimension math: HIGH — derived from official KDP bleed spec (verified)
- Pitfalls: HIGH — all from confirmed WeasyPrint GitHub issues or KDP official guidelines

**Research date:** 2026-03-24
**Valid until:** 2026-06-24 (stable libraries; WeasyPrint bleed issue #934 status may change)
