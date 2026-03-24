# Requirements: BookForge

**Defined:** 2026-03-24
**Core Value:** Consistent, high-quality children's book illustrations from a single markdown file — books that look hand-illustrated, not AI-generated, with characters recognizably the same across all pages.

## v1 Requirements

### CLI Foundation

- [x] **CLI-01**: User can run `uv run bookforge new <slug>` to scaffold a new book directory with story.md template
- [x] **CLI-02**: User can run `uv run bookforge illustrate <slug>` to generate images for all pages
- [ ] **CLI-03**: User can run `uv run bookforge build <slug>` to assemble HTML and export PDFs
- [ ] **CLI-04**: User can run `uv run bookforge review <slug>` to run pre-publish review checklist
- [ ] **CLI-05**: User can run `uv run bookforge publish <slug>` to generate publish package
- [ ] **CLI-06**: User can run `uv run bookforge calendar` to view upcoming release deadlines

### Story & Content

- [x] **STOR-01**: Story markdown format with YAML frontmatter (title, title_ko, slug, trim_size, price, ages)
- [x] **STOR-02**: Page boundaries defined by `## Page N` headers in story.md
- [x] **STOR-03**: English text is bare, Korean text wrapped in `<!-- ko -->` / `<!-- /ko -->` blocks
- [x] **STOR-04**: Image prompts embedded as `<!-- image: ... -->` comments per page
- [x] **STOR-05**: Claude API generates bilingual draft story from a one-line prompt via `new` command
- [x] **STOR-06**: Image prompt overrides saved as `<!-- image-override: ... -->` when using `--redo --prompt`

### Style & Consistency

- [x] **STYL-01**: Style guide YAML defines art style name, prompt prefix, color palette, negative prompt
- [x] **STYL-02**: Character definitions in style guide with visual description and reference image paths
- [x] **STYL-03**: Ho-rang (tiger) and Gom-i (bear) character sheets generated upfront as reference images
- [x] **STYL-04**: Every image generation call prepends style prefix + character descriptions + negative prompt
- [x] **STYL-05**: Image provider configured in style guide YAML (provider-agnostic layer)

### Image Generation

- [x] **IMG-01**: Flux Kontext Pro (via Replicate) as default image provider with character reference images
- [x] **IMG-02**: Abstract image provider interface allowing provider swap via config change
- [x] **IMG-03**: Generate one illustration per page (~10-12 per book) plus cover image
- [x] **IMG-04**: `--redo N,N` flag to regenerate specific pages without regenerating all
- [x] **IMG-05**: Image versioning — regenerated images saved alongside originals (page-03-v1.png, v2.png)
- [x] **IMG-06**: HTML contact sheet generated after illustration for quick visual review
- [x] **IMG-07**: Skip already-generated images on re-run (resume support)
- [x] **IMG-08**: Retry transient API failures up to 3 times with exponential backoff
- [x] **IMG-09**: Pin Replicate model version hash for reproducibility

### Build & PDF

- [ ] **BLD-01**: Three language editions from one story.md: `--lang en`, `--lang ko`, `--lang bilingual` (default)
- [ ] **BLD-02**: `--lang all` builds all 6 PDFs (3 editions x 2 formats)
- [ ] **BLD-03**: Screen PDF: RGB, no bleed, optimized for digital viewing (Gumroad)
- [ ] **BLD-04**: Print PDF: RGB with sRGB ICC profile (via pikepdf), 0.125" bleed, 300 DPI (KDP)
- [ ] **BLD-05**: HTML template with Jinja2 assembling story text + images per page
- [ ] **BLD-06**: Korean font (Noto Sans KR) embedded via @font-face for reliable CJK rendering
- [ ] **BLD-07**: No crop marks in print PDF (KDP rejects them)
- [ ] **BLD-08**: Default trim size 8.5x8.5" square, configurable per book in frontmatter

### Review & Publish

- [ ] **REV-01**: Review command shows summary (page count, image count, word count EN/KR, file sizes)
- [ ] **REV-02**: Review prints checklist (story quality, Korean proofread, image consistency, cover strength)
- [ ] **REV-03**: Review requires explicit `y/n` approval, stamps approval into book state
- [ ] **PUB-01**: Publish only runs if review approved
- [ ] **PUB-02**: Generates `publish-package/` with all PDFs, cover images (Gumroad thumb, KDP cover, 1080x1080 social)
- [ ] **PUB-03**: Auto-generates listing copy (title, description, price) for copy-paste into Gumroad/KDP
- [ ] **PUB-04**: KDP cover dimensions computed from trim size + spine width (based on page count + paper type)
- [ ] **PUB-05**: Step-by-step upload checklist including AI content disclosure reminder
- [ ] **PUB-06**: Spine width calculated at publish time from current page count

### Content Calendar

- [ ] **CAL-01**: content-calendar.yaml with holiday name, holiday date, release date, marketing start per book
- [ ] **CAL-02**: Calendar command displays upcoming releases with backward-planned deadlines
- [ ] **CAL-03**: Release dates target 2-3 weeks before holidays

## v2 Requirements

### Distribution

- **DIST-01**: IngramSpark formatting support (wider bookstore/library distribution)
- **DIST-02**: ePub format output
- **DIST-03**: Audio pronunciation of Korean words

### Marketing

- **MKT-01**: Social media image templates auto-generated per book
- **MKT-02**: Landing page / brand site for the series
- **MKT-03**: Gumroad bundle pricing (all 3 editions)

### Pipeline

- **PIPE-01**: Cost tracking per book (image generation spend)
- **PIPE-02**: Batch generation of multiple books
- **PIPE-03**: LoRA fine-tuning workflow for Ho-rang and Gom-i

## Out of Scope

| Feature | Reason |
|---------|--------|
| Web dashboard / GUI | CLI sufficient for 1 book/month; YAGNI |
| Automated Gumroad/KDP upload | No public APIs exist; ToS risk with browser automation |
| CMYK color space | WeasyPrint can't produce CMYK; KDP accepts sRGB and converts internally |
| Real-time collaboration | Single author + proofreader workflow; no need |
| Midjourney integration | No official API; unofficial wrappers violate ToS |
| Traditional publishing workflow | Build catalog and prove demand first |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CLI-01 | Phase 1 | Complete |
| CLI-02 | Phase 2 | Complete |
| CLI-03 | Phase 3 | Pending |
| CLI-04 | Phase 4 | Pending |
| CLI-05 | Phase 4 | Pending |
| CLI-06 | Phase 4 | Pending |
| STOR-01 | Phase 1 | Complete |
| STOR-02 | Phase 1 | Complete |
| STOR-03 | Phase 1 | Complete |
| STOR-04 | Phase 1 | Complete |
| STOR-05 | Phase 1 | Complete |
| STOR-06 | Phase 1 | Complete |
| STYL-01 | Phase 1 | Complete |
| STYL-02 | Phase 1 | Complete |
| STYL-03 | Phase 1 | Complete |
| STYL-04 | Phase 1 | Complete |
| STYL-05 | Phase 1 | Complete |
| IMG-01 | Phase 2 | Complete |
| IMG-02 | Phase 2 | Complete |
| IMG-03 | Phase 2 | Complete |
| IMG-04 | Phase 2 | Complete |
| IMG-05 | Phase 2 | Complete |
| IMG-06 | Phase 2 | Complete |
| IMG-07 | Phase 2 | Complete |
| IMG-08 | Phase 2 | Complete |
| IMG-09 | Phase 2 | Complete |
| BLD-01 | Phase 3 | Pending |
| BLD-02 | Phase 3 | Pending |
| BLD-03 | Phase 3 | Pending |
| BLD-04 | Phase 3 | Pending |
| BLD-05 | Phase 3 | Pending |
| BLD-06 | Phase 3 | Pending |
| BLD-07 | Phase 3 | Pending |
| BLD-08 | Phase 3 | Pending |
| REV-01 | Phase 4 | Pending |
| REV-02 | Phase 4 | Pending |
| REV-03 | Phase 4 | Pending |
| PUB-01 | Phase 4 | Pending |
| PUB-02 | Phase 4 | Pending |
| PUB-03 | Phase 4 | Pending |
| PUB-04 | Phase 4 | Pending |
| PUB-05 | Phase 4 | Pending |
| PUB-06 | Phase 4 | Pending |
| CAL-01 | Phase 4 | Pending |
| CAL-02 | Phase 4 | Pending |
| CAL-03 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 45 total
- Mapped to phases: 45
- Unmapped: 0

---
*Requirements defined: 2026-03-24*
*Last updated: 2026-03-24 after roadmap creation*
