---
phase: 2
slug: image-generation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-24
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | pyproject.toml (exists from Phase 1) |
| **Quick run command** | `uv run pytest tests/ -x -q` |
| **Full suite command** | `uv run pytest tests/ -v` |
| **Estimated runtime** | ~8 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -q`
- **After every plan wave:** Run `uv run pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 8 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01 | 01 | 1 | IMG-02 | unit | `uv run pytest tests/test_image_provider.py -x -v` | ❌ W0 | ⬜ pending |
| 02-02 | 01 | 1 | IMG-01 | unit | `uv run pytest tests/test_flux_provider.py -x -v` | ❌ W0 | ⬜ pending |
| 02-03 | 02 | 2 | CLI-02,IMG-03,IMG-07,IMG-08 | integration | `uv run pytest tests/test_illustrate.py -x -v` | ❌ W0 | ⬜ pending |
| 02-04 | 02 | 2 | IMG-04,IMG-05,IMG-06 | integration | `uv run pytest tests/test_illustrate.py -k redo_or_version_or_contact -x -v` | ❌ W0 | ⬜ pending |
| 02-05 | 02 | 2 | IMG-09 | unit | `uv run pytest tests/test_flux_provider.py -k version_pin -x -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_image_provider.py` — stubs for IMG-01, IMG-02
- [ ] `tests/test_flux_provider.py` — stubs for Flux Kontext specific behavior
- [ ] `tests/test_illustrate.py` — stubs for CLI illustrate command integration

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Character visual consistency | IMG-01 | Requires human visual inspection | Generate 3-5 test pages, open contact sheet, verify Ho-rang and Gom-i look consistent |
| Image aesthetic quality | IMG-01 | Subjective quality bar | Review contact sheet for "AI slop" indicators |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 8s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
