---
phase: 02-image-generation
plan: 01
subsystem: images
tags: [replicate, flux-kontext-pro, pillow, abc, provider-pattern]

requires:
  - phase: 01-foundation
    provides: StyleGuide with ImageConfig and CharacterDef reference_image paths
provides:
  - ImageProvider ABC with generate() and provider_name
  - ImageRequest/ImageResult dataclasses
  - ReplicateFluxKontextProvider with multi-character stitching
  - get_provider() factory for provider-agnostic instantiation
affects: [02-02-image-service, 03-build-pdf]

tech-stack:
  added: [replicate SDK async_run, Pillow image stitching]
  patterns: [provider ABC pattern, factory function, reference image stitching]

key-files:
  created:
    - bookforge/images/__init__.py
    - bookforge/images/provider.py
    - bookforge/images/providers/__init__.py
    - bookforge/images/providers/flux_kontext.py
    - tests/test_image_provider.py
    - tests/test_flux_provider.py
  modified: []

key-decisions:
  - "output_path added to ImageRequest dataclass for provider to write bytes directly"
  - "Aspect ratio derived from width/height via GCD reduction with fallback to 1:1"
  - "Stitched reference images use LANCZOS resampling for quality when heights differ"

patterns-established:
  - "Provider ABC pattern: ImageProvider with abstract generate() and provider_name"
  - "Factory pattern: get_provider(name) with lazy imports for concrete providers"
  - "Reference stitching: side-by-side Pillow composite into temp PNG for multi-character scenes"

requirements-completed: [IMG-01, IMG-02, IMG-09]

duration: 2min
completed: 2026-03-24
---

# Phase 2 Plan 1: Image Provider ABC and Flux Kontext Implementation Summary

**Provider-agnostic ImageProvider ABC with Replicate Flux Kontext Pro concrete implementation, multi-character reference stitching via Pillow, and version pinning**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-24T20:33:00Z
- **Completed:** 2026-03-24T20:35:14Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- ImageProvider ABC establishing the provider-agnostic interface for all image generation
- ReplicateFluxKontextProvider calling replicate.async_run with correct inputs, reference stitching, and version pinning
- Full test coverage with 12 tests (5 for ABC/factory, 7 for Flux provider)

## Task Commits

Each task was committed atomically:

1. **Task 1: ImageProvider ABC, dataclasses, and factory with tests** - `7e0fb13` (feat)
2. **Task 2: ReplicateFluxKontextProvider with reference stitching and version pinning** - `9206b14` (feat)

_Note: TDD tasks — tests written first (RED), then implementation (GREEN)._

## Files Created/Modified
- `bookforge/images/__init__.py` - Package init (empty)
- `bookforge/images/provider.py` - ImageProvider ABC, ImageRequest/ImageResult dataclasses
- `bookforge/images/providers/__init__.py` - get_provider() factory function
- `bookforge/images/providers/flux_kontext.py` - ReplicateFluxKontextProvider with stitching, version pinning
- `tests/test_image_provider.py` - 5 tests for ABC, dataclasses, factory
- `tests/test_flux_provider.py` - 7 tests for Flux provider (single/multi/no ref, pinning, bytes)

## Decisions Made
- Added `output_path` field to ImageRequest so providers write bytes directly to disk
- Aspect ratio derived from width/height via GCD reduction, defaulting to "1:1" for unmapped ratios
- Multi-ref stitching normalizes heights via LANCZOS resampling before side-by-side composite

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added output_path to ImageRequest**
- **Found during:** Task 2 (Flux provider implementation)
- **Issue:** Plan's ImageRequest had no output_path field, but provider needs to know where to write generated image bytes
- **Fix:** Added `output_path: Path` field to ImageRequest dataclass with sensible default
- **Files modified:** bookforge/images/provider.py
- **Verification:** All 12 tests pass
- **Committed in:** 9206b14 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Essential for provider to write output. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required. Replicate API key will be needed at runtime (handled by replicate SDK from REPLICATE_API_TOKEN env var).

## Next Phase Readiness
- ImageProvider ABC and Flux Kontext provider ready for ImageService orchestration in 02-02
- get_provider() factory can be called from CLI illustrate command
- Reference stitching tested and ready for multi-character scenes

---
*Phase: 02-image-generation*
*Completed: 2026-03-24*
