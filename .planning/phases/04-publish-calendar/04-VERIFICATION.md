---
phase: 04-publish-calendar
verified: 2026-03-24T21:35:00Z
status: passed
score: 15/15 must-haves verified
re_verification: false
---

# Phase 4: Publish Calendar Verification Report

**Phase Goal:** User can run the full end-of-pipeline workflow: review the book and stamp approval, generate a publish package with all PDFs and listing copy ready for manual upload, and view upcoming release deadlines from the content calendar
**Verified:** 2026-03-24T21:35:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #  | Truth                                                                                     | Status     | Evidence                                                                   |
|----|-------------------------------------------------------------------------------------------|------------|----------------------------------------------------------------------------|
| 1  | User can run `uv run bookforge review <slug>` and see page count, image count, word counts EN/KR, and file sizes | VERIFIED | `gather_summary()` returns all fields; CLI prints Rich table; 6 CLI tests pass |
| 2  | Review prints a checklist of items to verify                                              | VERIFIED   | `REVIEW_CHECKLIST` constant with 5 items in `review.py`; test confirms 5 items |
| 3  | Review prompts for explicit y/n approval and stamps result into state.json                | VERIFIED   | `typer.confirm()` in `cli/review.py`; stamps `review_approved`, `review_date`, `review_summary`; test `test_approve_stamps_state` passes |
| 4  | Re-running review after approval shows existing approval status without re-prompting      | VERIFIED   | `test_already_approved_shows_status` passes; code checks `state.get("review_approved")` |
| 5  | User can run `uv run bookforge calendar` and see upcoming releases in a Rich table        | VERIFIED   | `calendar_command` registered; `test_shows_upcoming_entries` passes       |
| 6  | Table shows holiday name, holiday date, release target date, and marketing start date     | VERIFIED   | `compute_deadlines()` provides all dates; `test_shows_computed_deadlines` passes |
| 7  | Release dates target 2-3 weeks before holidays                                            | VERIFIED   | `release_date = holiday - 21 days`; `test_release_date_21_days_before_holiday` passes |
| 8  | Calendar reads from content-calendar.yaml                                                 | VERIFIED   | `load_calendar(Path("content-calendar.yaml"))` in `cli/calendar.py`; `test_missing_yaml_shows_helpful_error` confirms error path |
| 9  | Publish refuses to run if review not approved (PUB-01)                                    | VERIFIED   | `if not state.get("review_approved")` in both `cli/publish.py` (line 31) and `publish/package.py` (line 89); `test_refuses_without_review` passes |
| 10 | Publish creates publish-package/ directory with all PDFs copied in                       | VERIFIED   | `create_publish_package()` copies `output/*.pdf`; `test_creates_full_package` passes |
| 11 | Publish generates cover images: Gumroad thumb (1600x2560), KDP cover with computed spine, 1080x1080 social | VERIFIED | All three generators in `covers.py`; pixel dimension tests pass |
| 12 | KDP spine width = page_count * 0.002252 inches (white paper)                             | VERIFIED   | `compute_spine_width()` at `covers.py:23`; `test_12_pages` (0.027024) and `test_100_pages` (0.2252) pass |
| 13 | Publish generates listing copy for Gumroad and KDP                                        | VERIFIED   | `generate_listing_copy()` returns `gumroad` and `kdp` keys with titles, descriptions, prices, keywords; 5 listing tests pass |
| 14 | Publish creates UPLOAD-CHECKLIST.md with AI content disclosure reminder                  | VERIFIED   | Jinja2 template at `assets/templates/UPLOAD-CHECKLIST.md` has AI Content Disclosure section; `test_ai_disclosure_section` passes |
| 15 | All artifacts zipped into publish-package.zip                                             | VERIFIED   | `shutil.make_archive` in `package.py`; `test_creates_zip` passes          |

**Score:** 15/15 truths verified

---

## Required Artifacts

| Artifact                                       | Expected                                          | Status   | Details                            |
|------------------------------------------------|---------------------------------------------------|----------|------------------------------------|
| `bookforge/review.py`                          | gather_summary(), REVIEW_CHECKLIST, format_summary() | VERIFIED | 71 lines; all three exports present |
| `bookforge/cli/review.py`                      | CLI review command with Typer                     | VERIFIED | 71 lines; review_command defined   |
| `bookforge/calendar.py`                        | CalendarEntry, load_calendar, compute_deadlines, get_upcoming | VERIFIED | 66 lines; all exports present |
| `bookforge/cli/calendar.py`                    | CLI calendar command                              | VERIFIED | 76 lines; calendar_command defined |
| `bookforge/publish/__init__.py`                | Package init                                      | VERIFIED | Present (intentionally empty)      |
| `bookforge/publish/covers.py`                  | compute_spine_width, generate_covers (3 variants) | VERIFIED | 126 lines; all generators present  |
| `bookforge/publish/listing.py`                 | generate_listing_copy, render_upload_checklist    | VERIFIED | 114 lines; both exports present    |
| `bookforge/publish/package.py`                 | create_publish_package()                          | VERIFIED | 136 lines; orchestrator present    |
| `bookforge/cli/publish.py`                     | CLI publish command                               | VERIFIED | 76 lines; publish_command defined  |
| `bookforge/assets/templates/UPLOAD-CHECKLIST.md` | Jinja2 template with AI disclosure             | VERIFIED | 34 lines; AI disclosure section present |
| `tests/test_review.py`                         | Unit tests for review logic                       | VERIFIED | 133 lines; 9 tests pass            |
| `tests/test_review_cli.py`                     | CLI integration tests for review                  | VERIFIED | 115 lines; 6 tests pass            |
| `tests/test_calendar.py`                       | Unit tests for calendar logic                     | VERIFIED | 161 lines; 12 tests pass           |
| `tests/test_calendar_cli.py`                   | CLI integration tests for calendar                | VERIFIED | 86 lines; 8 tests pass             |
| `tests/test_publish.py`                        | Unit tests for cover generation                   | VERIFIED | 93 lines; 6 tests pass             |
| `tests/test_listing.py`                        | Unit tests for listing copy                       | VERIFIED | 103 lines; 7 tests pass            |
| `tests/test_publish_cli.py`                    | CLI integration tests for publish                 | VERIFIED | 154 lines; 4 tests pass            |

---

## Key Link Verification

| From                          | To                           | Via                                                 | Status   | Details                                           |
|-------------------------------|------------------------------|-----------------------------------------------------|----------|---------------------------------------------------|
| `bookforge/cli/review.py`     | `bookforge/review.py`        | `from bookforge.review import gather_summary, REVIEW_CHECKLIST, format_summary` | WIRED | Line 12 confirmed |
| `bookforge/cli/review.py`     | `bookforge/state.py`         | `from bookforge.state import load_state, save_state` | WIRED | Line 13 confirmed |
| `bookforge/cli/__init__.py`   | `bookforge/cli/review.py`    | `app.command("review")(review_command)`             | WIRED    | Line 21 confirmed                                 |
| `bookforge/cli/calendar.py`   | `bookforge/calendar.py`      | `from bookforge.calendar import compute_deadlines, get_upcoming, load_calendar` | WIRED | Line 11 confirmed |
| `bookforge/cli/__init__.py`   | `bookforge/cli/calendar.py`  | `app.command("calendar")(calendar_command)`         | WIRED    | Line 22 confirmed                                 |
| `bookforge/cli/publish.py`    | `bookforge/state.py`         | checks `review_approved` before proceeding          | WIRED    | Line 31: `if not state.get("review_approved")`    |
| `bookforge/publish/covers.py` | `PIL`                        | `from PIL import Image, ImageDraw`                  | WIRED    | Line 13 confirmed                                 |
| `bookforge/publish/package.py`| `bookforge/publish/covers.py`| `from bookforge.publish.covers import ...`          | WIRED    | Lines 10-16 confirmed                             |
| `bookforge/publish/package.py`| `bookforge/publish/listing.py`| `from bookforge.publish.listing import generate_listing_copy, render_upload_checklist` | WIRED | Line 17 confirmed |
| `bookforge/cli/__init__.py`   | `bookforge/cli/publish.py`   | `app.command("publish")(publish_command)`           | WIRED    | Line 23 confirmed                                 |

---

## Requirements Coverage

| Requirement | Source Plan | Description                                                                          | Status    | Evidence                                                                |
|-------------|-------------|--------------------------------------------------------------------------------------|-----------|-------------------------------------------------------------------------|
| CLI-04      | 04-01       | User can run `uv run bookforge review <slug>` for pre-publish review checklist       | SATISFIED | Command registered; 15 tests cover all flows                            |
| REV-01      | 04-01       | Review shows summary (page count, image count, word count EN/KR, file sizes)         | SATISFIED | `gather_summary()` returns all 5 fields; Rich table renders them        |
| REV-02      | 04-01       | Review prints checklist (story quality, Korean proofread, image consistency, cover)  | SATISFIED | `REVIEW_CHECKLIST` has 5 items including all named categories           |
| REV-03      | 04-01       | Review requires explicit y/n approval, stamps approval into book state               | SATISFIED | `typer.confirm()` stamps `review_approved` + `review_date` into state.json |
| CLI-06      | 04-02       | User can run `uv run bookforge calendar` to view upcoming release deadlines          | SATISFIED | Command registered; 20 tests cover all calendar flows                   |
| CAL-01      | 04-02       | content-calendar.yaml with holiday name, date, release date, marketing start per book | SATISFIED | `CalendarEntry` model + `load_calendar()` reads this format             |
| CAL-02      | 04-02       | Calendar command displays upcoming releases with backward-planned deadlines          | SATISFIED | `compute_deadlines()` + `get_upcoming()` + Rich table render            |
| CAL-03      | 04-02       | Release dates target 2-3 weeks before holidays                                       | SATISFIED | `release_date = holiday_date - timedelta(days=21)`                      |
| CLI-05      | 04-03       | User can run `uv run bookforge publish <slug>` to generate publish package           | SATISFIED | Command registered; 4 CLI tests pass                                    |
| PUB-01      | 04-03       | Publish only runs if review approved                                                 | SATISFIED | Gate check in both `cli/publish.py` and `publish/package.py`           |
| PUB-02      | 04-03       | Generates publish-package/ with all PDFs, cover images (Gumroad, KDP, 1080x1080)    | SATISFIED | `create_publish_package()` orchestrates all three cover generators      |
| PUB-03      | 04-03       | Auto-generates listing copy for Gumroad/KDP                                          | SATISFIED | `generate_listing_copy()` returns structured listings for both platforms |
| PUB-04      | 04-03       | KDP cover dimensions computed from trim size + spine width (page count + paper type) | SATISFIED | `compute_kdp_cover_dimensions()` uses trim + computed spine             |
| PUB-05      | 04-03       | Step-by-step upload checklist including AI content disclosure reminder               | SATISFIED | Jinja2 template has explicit AI Content Disclosure section              |
| PUB-06      | 04-03       | Spine width calculated at publish time from current page count                       | SATISFIED | `compute_spine_width(page_count)` called in `create_publish_package()`  |

**All 15 requirement IDs accounted for. No orphaned requirements.**

---

## Anti-Patterns Found

No blockers or warnings. One false-positive flagged and resolved:

- `bookforge/review.py` line 16: `"No placeholder text or TODO markers remain"` — this is checklist copy, not a code stub.

---

## Test Results

**52 tests, 52 passed, 0 failed** across all 7 test files.

```
tests/test_review.py         9 passed
tests/test_review_cli.py     6 passed
tests/test_calendar.py      12 passed
tests/test_calendar_cli.py   8 passed
tests/test_publish.py        6 passed
tests/test_listing.py        7 passed
tests/test_publish_cli.py    4 passed
```

---

## Human Verification Required

### 1. Rich table visual rendering

**Test:** Run `uv run bookforge review <slug>` against a real book directory and inspect the terminal output.
**Expected:** Summary table with page count, image count, EN/KR word counts, and PDF sizes renders without truncation.
**Why human:** Table formatting and terminal width behavior cannot be fully verified by CliRunner.

### 2. Approval prompt interaction

**Test:** Run `uv run bookforge review <slug>` and respond to the y/n prompt interactively.
**Expected:** Prompt appears, y stamps state.json, n exits cleanly with "Review not approved." message.
**Why human:** CliRunner simulates input; real TTY prompt behavior (cursor, input echo) needs manual check.

### 3. KDP cover image quality

**Test:** Run `uv run bookforge publish <slug>` against an approved book and inspect `kdp-cover.png`.
**Expected:** Full spread image with back cover (dominant color fill), narrow spine strip, and front cover image all composited correctly at 300 DPI.
**Why human:** Pillow image pixel dimensions are tested, but visual correctness of the composite layout requires inspection.

### 4. content-calendar.yaml with real dates

**Test:** Create a `content-calendar.yaml` with upcoming holidays and run `uv run bookforge calendar`.
**Expected:** Table shows only future holidays by default; `--all` shows past ones; dates in all columns are correct.
**Why human:** Relative date filtering (get_upcoming compares against today) needs verification with real calendar data.

---

## Summary

Phase 4 goal is fully achieved. All 15 must-have truths verified against actual code. All 15 requirement IDs (CLI-04, CLI-05, CLI-06, REV-01, REV-02, REV-03, PUB-01, PUB-02, PUB-03, PUB-04, PUB-05, PUB-06, CAL-01, CAL-02, CAL-03) are satisfied by substantive, wired implementations. 52 automated tests pass. The three CLI commands (`review`, `publish`, `calendar`) are registered and functional. No stubs, no orphaned code, no anti-patterns.

Four items are flagged for optional human verification — they are presentation and integration checks, not functional gaps.

---

_Verified: 2026-03-24T21:35:00Z_
_Verifier: Claude (gsd-verifier)_
