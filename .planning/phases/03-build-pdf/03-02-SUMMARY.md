---
phase: 03-build-pdf
plan: 02
subsystem: build
tags: [weasyprint, pikepdf, pdf, cli, korean-font, icc, kdp]

requires:
  - phase: 03-01
    provides: render_book_html() HTML renderer and Jinja2 templates
provides:
  - build_pdf() WeasyPrint HTML-to-PDF with FontConfiguration
  - patch_print_pdf() pikepdf TrimBox/BleedBox/ICC injection
  - CLI build command with --lang and --format options
affects: [04-polish]

tech-stack:
  added: [weasyprint, pikepdf]
  patterns: [two-pass-pdf-pipeline, pikepdf-output-intent, font-config-dual-pass]

key-files:
  created:
    - bookforge/build/pdf.py
    - bookforge/build/postprocess.py
    - bookforge/cli/build.py
    - tests/test_pdf_export.py
    - tests/test_build_cli.py
  modified:
    - bookforge/cli/__init__.py

key-decisions:
  - "WeasyPrint natively sets TrimBox/BleedBox -- screen PDF test checks for absence of ICC OutputIntent rather than absence of boxes"
  - "Print post-processing overwrites WeasyPrint boxes with computed values from trim_inches and bleed_inches parameters"
  - "Default build is bilingual edition (screen+print), not all 6 editions"

patterns-established:
  - "Two-pass PDF: WeasyPrint renders HTML, pikepdf post-processes for print compliance"
  - "FontConfiguration passed to both CSS() and write_pdf() for Korean font support"
  - "CLI build pattern: parse trim_size from book meta, get bleed from style guide"

requirements-completed: [CLI-03, BLD-02, BLD-03, BLD-04, BLD-07]

duration: 4min
completed: 2026-03-24
---

# Phase 3 Plan 2: PDF Export & CLI Build Summary

**WeasyPrint PDF export with pikepdf print post-processing (TrimBox/BleedBox/sRGB ICC) and CLI build command supporting --lang and --format options**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-24T21:06:03Z
- **Completed:** 2026-03-24T21:10:03Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- build_pdf() renders HTML to PDF via WeasyPrint with FontConfiguration for Korean text
- patch_print_pdf() sets correct MediaBox/TrimBox/BleedBox and embeds sRGB ICC OutputIntent for KDP compliance
- CLI `bookforge build` command with --lang (en/ko/bilingual/all) and --format (screen/print/all) options
- 14 tests covering PDF generation, post-processing dimensions, ICC embedding, and all CLI option combinations

## Task Commits

Each task was committed atomically:

1. **Task 1: PDF export module and pikepdf post-processing** - `b856081` (feat)
2. **Task 2: CLI build command with --lang and --format options** - `428e311` (feat)

_Both tasks used TDD: tests written first (RED), then implementation (GREEN)._

## Files Created/Modified
- `bookforge/build/pdf.py` - build_pdf() WeasyPrint rendering with FontConfiguration
- `bookforge/build/postprocess.py` - patch_print_pdf() pikepdf TrimBox/BleedBox/ICC injection
- `bookforge/cli/build.py` - CLI build command orchestrating edition/format combinations
- `bookforge/cli/__init__.py` - Registered build command
- `tests/test_pdf_export.py` - 7 tests for PDF export and post-processing
- `tests/test_build_cli.py` - 7 integration tests for CLI build command

## Decisions Made
- WeasyPrint natively adds TrimBox/BleedBox to all PDFs -- adjusted screen test to check for ICC OutputIntent absence instead of box absence
- Print post-processing overwrites WeasyPrint's native boxes with computed values from parameters
- Default build is bilingual edition (screen+print), matching the most common use case

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Adjusted screen PDF test assertion**
- **Found during:** Task 1 (test_screen_pdf_not_postprocessed)
- **Issue:** WeasyPrint natively sets TrimBox/BleedBox on all PDFs, so checking for their absence is incorrect for screen PDFs
- **Fix:** Changed test to verify absence of sRGB OutputIntent (which is only added by our post-processing) instead of box absence
- **Files modified:** tests/test_pdf_export.py
- **Verification:** All 7 PDF export tests pass
- **Committed in:** b856081 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor test adjustment, no scope creep.

## Issues Encountered
None beyond the deviation noted above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Full PDF build pipeline complete: story.md -> HTML -> PDF (screen + print)
- Ready for Phase 4 (polish/integration testing)
- Print PDFs have KDP-compliant TrimBox/BleedBox and sRGB ICC OutputIntent

---
*Phase: 03-build-pdf*
*Completed: 2026-03-24*
