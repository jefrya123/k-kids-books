# Roadmap: BookForge

## Overview

BookForge is built in four phases that follow the natural dependency order of the pipeline: foundation first (story format, style guide, CLI scaffold), then image generation (the highest technical risk — validate Flux Kontext character consistency before building on top of it), then PDF build (all six output variants, KDP-compliant), then the final packaging and scheduling layer (review gate, publish package, content calendar). Each phase delivers a complete, independently verifiable capability.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation** - CLI scaffold, story markdown format, style guide loader, and project state management (completed 2026-03-24)
- [ ] **Phase 2: Image Generation** - Flux Kontext illustration pipeline with resume, retry, and character reference conditioning
- [ ] **Phase 3: Build & PDF** - HTML assembly and all six PDF variants (3 editions x screen/print) with KDP compliance
- [ ] **Phase 4: Publish & Calendar** - Review gate, publish package generation, listing copy, and content calendar

## Phase Details

### Phase 1: Foundation
**Goal**: User can scaffold a new book project, write/generate a bilingual story, and have that story parsed into a validated data structure ready for illustration
**Depends on**: Nothing (first phase)
**Requirements**: CLI-01, STOR-01, STOR-02, STOR-03, STOR-04, STOR-05, STOR-06, STYL-01, STYL-02, STYL-03, STYL-04, STYL-05
**Success Criteria** (what must be TRUE):
  1. User can run `uv run bookforge new <slug>` and get a scaffolded book directory with a populated story.md template and style guide YAML
  2. User can run `uv run bookforge new <slug> --prompt "..."` and get a Claude-generated bilingual English/Korean story draft in the correct markdown format
  3. A story.md file with YAML frontmatter, page boundaries, bilingual text blocks, and image prompts parses without error into a validated Book dataclass
  4. Style guide YAML with character definitions, prompt prefix, color palette, and provider config loads and validates via Pydantic at startup
  5. Character reference image paths defined in the style guide are resolved and accessible before any illustration command runs
**Plans**: 4 plans

Plans:
- [x] 01-01-PLAN.md — Project scaffold, Pydantic schemas, test fixtures
- [x] 01-02-PLAN.md — Story parser and validator
- [x] 01-03-PLAN.md — Style guide loader and default style guide YAML
- [x] 01-04-PLAN.md — CLI new command and Claude story generator

### Phase 2: Image Generation
**Goal**: User can run `uv run bookforge illustrate <slug>` and get one AI-generated illustration per page with consistent character appearance, with the ability to resume interrupted runs and redo specific pages
**Depends on**: Phase 1
**Requirements**: CLI-02, IMG-01, IMG-02, IMG-03, IMG-04, IMG-05, IMG-06, IMG-07, IMG-08, IMG-09
**Success Criteria** (what must be TRUE):
  1. User can run `uv run bookforge illustrate <slug>` and all pages generate illustrations via Flux Kontext Pro with the style prefix and character reference images applied to every call
  2. Re-running `illustrate` on a partially completed book skips already-generated pages and only generates the missing ones
  3. User can run `illustrate --redo 3,7` to regenerate only pages 3 and 7 without touching other pages; regenerated images are saved as versioned files (page-03-v2.png)
  4. Transient Replicate API failures retry up to 3 times with exponential backoff; the run does not abort on a single page failure
  5. An HTML contact sheet is generated after illustration completes, showing all page images for quick visual review of character consistency
**Plans**: 2 plans

Plans:
- [ ] 02-01-PLAN.md — ImageProvider ABC, Flux Kontext provider, factory, version pinning
- [ ] 02-02-PLAN.md — ImageService orchestration, CLI illustrate command, contact sheet

### Phase 3: Build & PDF
**Goal**: User can run `uv run bookforge build <slug>` and get all six PDFs — three language editions in both screen and print formats — with correct Korean text rendering, KDP-compliant bleed and DPI, and no crop marks
**Depends on**: Phase 2
**Requirements**: CLI-03, BLD-01, BLD-02, BLD-03, BLD-04, BLD-05, BLD-06, BLD-07, BLD-08
**Success Criteria** (what must be TRUE):
  1. User can run `uv run bookforge build <slug>` and get six PDF files: English screen, Korean screen, bilingual screen, English print, Korean print, bilingual print
  2. Korean text renders correctly (no blank glyphs) using the bundled Noto Sans KR font in all Korean and bilingual editions
  3. Print PDFs have 0.125" bleed on all edges, no crop marks, and an embedded sRGB ICC profile — passing KDP's online PDF previewer without rejection
  4. Screen PDFs are RGB with no bleed, sized correctly for digital viewing on Gumroad
  5. `--lang all` builds all six variants in a single command; `--lang en` builds only the two English-edition PDFs
**Plans**: TBD

Plans:
- [ ] 03-01: TBD

### Phase 4: Publish & Calendar
**Goal**: User can run the full end-of-pipeline workflow: review the book and stamp approval, generate a publish package with all PDFs and listing copy ready for manual upload, and view upcoming release deadlines from the content calendar
**Depends on**: Phase 3
**Requirements**: CLI-04, CLI-05, CLI-06, REV-01, REV-02, REV-03, PUB-01, PUB-02, PUB-03, PUB-04, PUB-05, PUB-06, CAL-01, CAL-02, CAL-03
**Success Criteria** (what must be TRUE):
  1. User can run `uv run bookforge review <slug>` and see a summary (page count, image count, word counts, file sizes) plus a checklist; the command requires explicit y/n approval and stamps the result into book state
  2. `uv run bookforge publish <slug>` refuses to run if review has not been approved, and when run on an approved book produces a `publish-package/` directory with all six PDFs, cover images (Gumroad thumb, KDP cover, 1080x1080 social), and a zipped archive
  3. The publish package includes Gumroad and KDP listing copy (title, description, price) ready to copy-paste, with correct KDP cover dimensions and spine width calculated from page count
  4. The publish package includes an UPLOAD-CHECKLIST.md with a step-by-step upload guide and an explicit AI content disclosure reminder
  5. User can run `uv run bookforge calendar` and see upcoming release deadlines with holiday names, holiday dates, release target dates, and marketing start dates in a Rich table
**Plans**: TBD

Plans:
- [ ] 04-01: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 4/4 | Complete    | 2026-03-24 |
| 2. Image Generation | 1/2 | In Progress|  |
| 3. Build & PDF | 0/? | Not started | - |
| 4. Publish & Calendar | 0/? | Not started | - |
