---
phase: 04-publish-calendar
plan: 02
subsystem: cli
tags: [calendar, rich, ruamel-yaml, pydantic, typer, deadline-planning]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: CLI registration pattern, ruamel.yaml usage pattern
provides:
  - CalendarEntry Pydantic model for content calendar entries
  - load_calendar YAML loader with sorting
  - compute_deadlines backward-planned date computation
  - get_upcoming date filter
  - CLI calendar command with Rich table output
affects: [04-publish-calendar]

# Tech tracking
tech-stack:
  added: []
  patterns: [Rich Table for CLI output, backward deadline computation from holiday dates]

key-files:
  created:
    - bookforge/calendar.py
    - bookforge/cli/calendar.py
    - tests/test_calendar.py
    - tests/test_calendar_cli.py
  modified:
    - bookforge/cli/__init__.py

key-decisions:
  - "Console width=200 to prevent Rich table truncation in narrow terminals"
  - "Pydantic BaseModel for CalendarEntry instead of dataclass for consistency with rest of codebase"

patterns-established:
  - "Rich Table pattern: Console(width=200) + no_wrap=True columns for CLI table output"
  - "Backward deadline computation: fixed offsets from holiday_date (21d release, 35d marketing, 42d illustration, 56d writing)"

requirements-completed: [CLI-06, CAL-01, CAL-02, CAL-03]

# Metrics
duration: 3min
completed: 2026-03-24
---

# Phase 4 Plan 2: Calendar Command Summary

**Content calendar CLI with Rich table showing backward-planned release deadlines from content-calendar.yaml**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-24T21:19:11Z
- **Completed:** 2026-03-24T21:22:27Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- CalendarEntry Pydantic model with YAML loader, date sorting, and upcoming filter
- Backward deadline computation (release -21d, marketing -35d, illustration -42d, writing -56d)
- Rich table CLI command with --all flag for past entries and helpful error on missing YAML
- 20 TDD tests covering data model, deadlines, CLI output, filtering, and error handling

## Task Commits

Each task was committed atomically:

1. **Task 1: Calendar data model, YAML loader, and backward deadline computation** - `7208af8` (feat)
2. **Task 2: CLI calendar command with Rich table output** - `e729ae4` (feat)

_Note: TDD tasks -- tests written first (RED), then implementation (GREEN)._

## Files Created/Modified
- `bookforge/calendar.py` - CalendarEntry model, load_calendar, compute_deadlines, get_upcoming
- `bookforge/cli/calendar.py` - CLI calendar command with Rich table rendering
- `bookforge/cli/__init__.py` - Registered calendar command
- `tests/test_calendar.py` - 12 unit tests for calendar logic and date math
- `tests/test_calendar_cli.py` - 8 CLI integration tests for calendar command

## Decisions Made
- Console width=200 to prevent Rich table truncation in CliRunner's narrow terminal
- Pydantic BaseModel for CalendarEntry (consistent with style schema pattern)
- JSON round-trip for ruamel CommentedMap to plain dict (same pattern as style loader)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Rich table truncation in narrow terminal**
- **Found during:** Task 2 (CLI tests)
- **Issue:** Rich Console defaulted to narrow width in CliRunner, truncating holiday names and dates
- **Fix:** Set Console(width=200) and no_wrap=True on all table columns
- **Files modified:** bookforge/cli/calendar.py
- **Verification:** All 8 CLI tests pass with full text visible
- **Committed in:** e729ae4 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor display fix, no scope creep.

## Issues Encountered
None beyond the Rich table width issue documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Calendar command ready for use with any content-calendar.yaml
- Phase 4 Plan 3 (publish) can proceed independently

---
*Phase: 04-publish-calendar*
*Completed: 2026-03-24*
