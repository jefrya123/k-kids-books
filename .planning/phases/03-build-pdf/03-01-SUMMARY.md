---
phase: 03-build-pdf
plan: 01
subsystem: build
tags: [jinja2, weasyprint, korean-font, css-paged-media, html-templates]

requires:
  - phase: 01-foundation
    provides: Book/Page/BilingualText/BookMeta schema models
  - phase: 01-foundation
    provides: StyleGuide/Layout schema models
provides:
  - render_book_html(book, edition, style_guide, fmt, book_dir) -> HTML string
  - Jinja2 templates with edition-aware text filtering (en/ko/bilingual)
  - CSS stylesheets for screen (no bleed) and print (bleed + marks:none)
  - Bundled NotoSansKR-Regular.otf font for @font-face Korean rendering
  - Bundled sRGB ICC profile for print PDF OutputIntent
affects: [03-build-pdf plan 02, pdf-generation, cli-build-command]

tech-stack:
  added: [jinja2, weasyprint, pikepdf]
  patterns: [Jinja2 FileSystemLoader templates, edition variable filtering, CSS Jinja2 variables for dimensions]

key-files:
  created:
    - bookforge/build/__init__.py
    - bookforge/build/renderer.py
    - bookforge/assets/templates/book_base.html.j2
    - bookforge/assets/templates/book_page.html.j2
    - bookforge/assets/templates/css/base.css
    - bookforge/assets/templates/css/screen.css
    - bookforge/assets/templates/css/print.css
    - bookforge/assets/fonts/NotoSansKR-Regular.otf
    - bookforge/assets/icc/sRGB_v4_ICC_preference.icc
    - tests/test_template.py
  modified:
    - pyproject.toml
    - uv.lock

key-decisions:
  - "Used system sRGB.icc from colord package (color.org download blocked by 403)"
  - "Single Jinja2 template with edition variable for language filtering via != conditionals"
  - "CSS dimensions injected as Jinja2 variables -- no hardcoded sizes"
  - "Font path resolved as file:// URI for WeasyPrint compatibility"

patterns-established:
  - "Edition filtering: {% if edition != 'ko' %} for English, {% if edition != 'en' %} for Korean"
  - "Format switching: fmt variable selects screen.css or print.css via Jinja2 conditional include"
  - "Dimension derivation: trim_size parsed to floats, bleed added for print format only"

requirements-completed: [BLD-05, BLD-06, BLD-08, BLD-01]

duration: 5min
completed: 2026-03-24
---

# Phase 3 Plan 1: HTML Templates & Renderer Summary

**Jinja2 HTML renderer with edition-aware text filtering, NotoSansKR font, screen/print CSS, and sRGB ICC profile**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-24T20:57:54Z
- **Completed:** 2026-03-24T21:03:04Z
- **Tasks:** 2
- **Files modified:** 12

## Accomplishments
- render_book_html() produces valid HTML for all 6 combinations (3 editions x 2 formats)
- Edition filtering works correctly: en-only omits Korean, ko-only omits English, bilingual shows both
- Print CSS includes bleed (0.125in) and marks:none for KDP compliance
- Screen CSS has no bleed properties -- clean digital output
- All dimensions derived from BookMeta.trim_size and StyleGuide.layout, not hardcoded
- Bundled NotoSansKR-Regular.otf (10MB KR-only variant) and sRGB ICC profile (16KB)

## Task Commits

Each task was committed atomically:

1. **Task 1: Bundle font/ICC assets and create Jinja2 templates + CSS** - `56910ab` (feat)
2. **Task 2: Build renderer module with render_book_html()** - `cbf486c` (feat)

_Note: TDD tasks -- tests written first (RED), then implementation (GREEN)_

## Files Created/Modified
- `bookforge/build/renderer.py` - render_book_html() function with Jinja2 template rendering
- `bookforge/build/__init__.py` - Build module init
- `bookforge/assets/templates/book_base.html.j2` - Base HTML document with CSS includes
- `bookforge/assets/templates/book_page.html.j2` - Per-page template with edition filtering
- `bookforge/assets/templates/css/base.css` - @font-face, typography, page layout
- `bookforge/assets/templates/css/screen.css` - Screen format (trim-only, no bleed)
- `bookforge/assets/templates/css/print.css` - Print format (bleed + marks:none)
- `bookforge/assets/fonts/NotoSansKR-Regular.otf` - Korean font for @font-face
- `bookforge/assets/icc/sRGB_v4_ICC_preference.icc` - sRGB ICC profile for print OutputIntent
- `tests/test_template.py` - 17 unit tests covering assets, CSS, templates, and renderer
- `pyproject.toml` - Added jinja2, weasyprint, pikepdf dependencies

## Decisions Made
- Used system sRGB.icc from colord package because color.org direct downloads return 403
- Single Jinja2 template with edition variable for language filtering (not separate templates per edition)
- CSS dimensions injected as Jinja2 variables so all sizes derive from config
- Font path resolved as file:// URI for WeasyPrint compatibility

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed "bleed" appearing in CSS comments for screen format**
- **Found during:** Task 1
- **Issue:** CSS comments in base.css and screen.css contained the word "bleed", causing false positive in screen-no-bleed assertion
- **Fix:** Rewrote comments to avoid the word "bleed" in base.css and screen.css
- **Files modified:** bookforge/assets/templates/css/base.css, bookforge/assets/templates/css/screen.css
- **Committed in:** 56910ab (Task 1 commit)

**2. [Rule 1 - Bug] Fixed test assertion for screen-no-bleed checking too broadly**
- **Found during:** Task 2
- **Issue:** pytest tmp_path contained "bleed" in directory name (test_screen_format_no_bleed0), causing false positive in `assert "bleed" not in html`
- **Fix:** Changed assertion to check for CSS property `"bleed:"` instead of bare string `"bleed"`
- **Files modified:** tests/test_template.py
- **Committed in:** cbf486c (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both fixes necessary for correct test assertions. No scope creep.

## Issues Encountered
- color.org blocks direct ICC profile downloads with 403 -- used system colord sRGB.icc instead (functionally identical)

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- HTML renderer ready for WeasyPrint PDF generation (plan 03-02)
- Font and ICC assets bundled for PDF pipeline
- All 6 edition/format combinations produce correct HTML

---
*Phase: 03-build-pdf*
*Completed: 2026-03-24*
