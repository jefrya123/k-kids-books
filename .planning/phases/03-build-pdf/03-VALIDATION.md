---
phase: 3
slug: build-pdf
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-24
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | pyproject.toml (exists) |
| **Quick run command** | `uv run pytest tests/ -x -q` |
| **Full suite command** | `uv run pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -q`
- **After every plan wave:** Run `uv run pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01 | 01 | 1 | BLD-05,BLD-06,BLD-08 | unit | `uv run pytest tests/test_template.py -x -v` | ❌ W0 | ⬜ pending |
| 03-02 | 01 | 1 | BLD-01 | unit | `uv run pytest tests/test_template.py -k lang -x -v` | ❌ W0 | ⬜ pending |
| 03-03 | 02 | 2 | BLD-03,BLD-04,BLD-07 | unit | `uv run pytest tests/test_pdf_export.py -x -v` | ❌ W0 | ⬜ pending |
| 03-04 | 02 | 2 | CLI-03,BLD-02 | integration | `uv run pytest tests/test_build_cli.py -x -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_template.py` — stubs for Jinja2 template rendering + language filtering
- [ ] `tests/test_pdf_export.py` — stubs for WeasyPrint + pikepdf PDF generation
- [ ] `tests/test_build_cli.py` — stubs for CLI build command

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Korean text renders visually | BLD-06 | Font rendering is visual | Open a generated bilingual PDF, confirm Korean glyphs display correctly |
| Print PDF passes KDP previewer | BLD-04 | External tool validation | Upload print PDF to KDP previewer, check for rejection errors |
| Bleed extends to edge | BLD-04 | Visual inspection | Open print PDF, verify illustrations extend into bleed area |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
