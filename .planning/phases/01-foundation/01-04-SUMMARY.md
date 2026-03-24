---
phase: 01-foundation
plan: 04
subsystem: cli
tags: [typer, anthropic, streaming, claude, cli]

requires:
  - phase: 01-02
    provides: story parser and validator
  - phase: 01-03
    provides: style guide loader and schema
provides:
  - generate_story() function calling Claude API with streaming
  - bookforge new CLI command for scaffolding book directories
  - End-to-end flow from prompt to story.md + state.json
affects: [02-image-generation, cli-commands]

tech-stack:
  added: [anthropic-sdk-streaming]
  patterns: [typer-command-registration, mock-streaming-context-manager]

key-files:
  created:
    - bookforge/story/generator.py
    - bookforge/cli/new.py
    - tests/test_generator.py
    - tests/test_new_command.py
  modified:
    - bookforge/cli/__init__.py

key-decisions:
  - "generate_story uses positional+keyword args matching research pattern for clean call sites"
  - "Rich console for styled CLI output with progress feedback"

patterns-established:
  - "CLI command pattern: separate module per command, registered via app.command() in __init__.py"
  - "API mock pattern: mock anthropic.Anthropic class, provide stream context manager with get_final_text()"

requirements-completed: [CLI-01, STOR-05]

duration: 2min
completed: 2026-03-24
---

# Phase 1 Plan 4: New Command and Story Generator Summary

**Claude streaming story generator with `bookforge new <slug>` CLI command scaffolding complete book directories**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-24T20:11:33Z
- **Completed:** 2026-03-24T20:13:40Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Claude story generator with streaming API calls and configurable model
- `bookforge new` CLI command that scaffolds book directories with story.md and state.json
- 17 new tests (9 generator + 8 CLI) all passing with mocked API, 57 total suite

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement Claude story generator with streaming** - `dde14e8` (feat)
2. **Task 2: Implement bookforge new CLI command** - `61a7b85` (feat)

_Both tasks followed TDD: RED (failing tests) then GREEN (implementation)._

## Files Created/Modified
- `bookforge/story/generator.py` - Claude API streaming story generation with SYSTEM_PROMPT
- `bookforge/cli/new.py` - Typer command: scaffold directory, generate story, init state
- `bookforge/cli/__init__.py` - Register new_command on app
- `tests/test_generator.py` - 9 mocked tests for streaming, model selection, output format
- `tests/test_new_command.py` - 8 tests for directory creation, state, error handling, options

## Decisions Made
- Used Rich console for styled CLI output (already a Typer dependency, zero cost)
- generate_story() takes style_guide_name as keyword arg for clarity at call sites
- SYSTEM_PROMPT uses .format() for page_count and ages interpolation (simple, readable)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required. ANTHROPIC_API_KEY is needed at runtime but tests use mocks.

## Next Phase Readiness
- Foundation phase complete: schemas, parser, validator, style loader, generator, and CLI all wired together
- Ready for Phase 2 (image generation) which will add `bookforge illustrate` command
- Risk note: ANTHROPIC_API_KEY must be set for live usage (tested via mock only)

---
*Phase: 01-foundation*
*Completed: 2026-03-24*
