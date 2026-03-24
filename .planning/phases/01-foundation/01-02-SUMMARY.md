---
phase: 01-foundation
plan: 02
subsystem: story-parsing
tags: [python-frontmatter, regex, pydantic, parser, validator, bilingual]

requires:
  - phase: 01-foundation-01
    provides: "Pydantic schemas (Book, BookMeta, Page, BilingualText) and test fixtures"
provides:
  - "parse_story(path) -> Book function for loading story.md files"
  - "validate_book(book) -> list[str] soft validator for completeness checks"
affects: [01-foundation-03, 01-foundation-04, 02-illustration, 03-pdf-build]

tech-stack:
  added: [python-frontmatter]
  patterns: [targeted-comment-extraction, soft-validation-pattern]

key-files:
  created:
    - bookforge/story/parser.py
    - bookforge/story/validator.py
  modified:
    - tests/test_story_parser.py

key-decisions:
  - "Targeted comment removal in _extract_en() -- only strips ko/image/image-override comments, preserves all other HTML comments (Pitfall 1 fix)"
  - "Soft validator returns warning strings instead of raising exceptions -- CLI can display warnings without blocking"

patterns-established:
  - "Targeted extraction: remove only known structured comments, never blanket-strip HTML"
  - "Soft validation: validate_book returns list[str] warnings, not exceptions"

requirements-completed: [STOR-02, STOR-03, STOR-04]

duration: 2min
completed: 2026-03-24
---

# Phase 1 Plan 2: Story Parser Summary

**story.md parser with targeted comment extraction and soft completeness validator -- handles bilingual text, image prompts, overrides, and multi-line prompts**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-24T20:06:26Z
- **Completed:** 2026-03-24T20:08:50Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- parse_story() correctly parses YAML frontmatter + page sections into validated Book model
- English extraction preserves non-structural HTML comments (Pitfall 1 addressed)
- validate_book() reports per-page completeness issues with descriptive messages
- 15 parser/validator tests, 40 total suite tests all green

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement story parser** - `413c443` (test) -> `fb06767` (feat)
2. **Task 2: Implement story validator** - `750b20f` (test) -> `639e3d2` (feat)

_TDD: each task has RED (test) and GREEN (feat) commits._

## Files Created/Modified
- `bookforge/story/parser.py` - parse_story() with _extract_en/ko/image/image_override helpers
- `bookforge/story/validator.py` - validate_book() soft completeness checker
- `tests/test_story_parser.py` - 15 tests covering parsing, overrides, edge cases, validation

## Decisions Made
- Targeted comment removal: _extract_en() removes only ko/image/image-override comments, preserving any regular HTML comments in English prose (Pitfall 1 from research)
- Soft validator pattern: validate_book() returns warning strings rather than raising exceptions, allowing CLI to display issues without blocking the pipeline

## Deviations from Plan

None -- plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None -- no external service configuration required.

## Next Phase Readiness
- parse_story() is ready for use by CLI commands (plan 03/04)
- validate_book() available for CLI `bookforge check` or pre-illustration validation
- Schema + parser + validator form complete story data pipeline foundation

---
*Phase: 01-foundation*
*Completed: 2026-03-24*

## Self-Check: PASSED
