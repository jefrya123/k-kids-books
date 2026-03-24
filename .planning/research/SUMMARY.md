# Project Research Summary

**Project:** BookForge — Bilingual Korean Children's Book Pipeline
**Domain:** AI-illustrated bilingual children's book production (Python CLI tool)
**Researched:** 2026-03-24
**Confidence:** HIGH (stack verified via PyPI; KDP/Gumroad specs from official sources; architecture follows well-established Python patterns)

## Executive Summary

BookForge is a linear stage pipeline CLI that takes a bilingual story markdown file and produces print-ready and screen PDFs for KDP and Gumroad distribution. Expert practice for this domain is: generate story via Claude, generate illustrations via Flux Kontext with character reference images, assemble HTML via Jinja2, export PDFs via WeasyPrint, post-process print PDFs via pikepdf for KDP compliance, and package listing copy for manual upload. Human review gates at story approval and final PDF approval are essential — both for quality and because illustration generation costs real money. The entire pipeline is orchestrated by a Typer CLI with per-project state persistence in a JSON file.

The recommended approach is a bottom-up build order: state management and schema first, then story parsing, then image generation (the highest technical risk), then PDF build, then publish packaging. Character consistency across 20+ pages via Flux Kontext reference-image conditioning is the central technical challenge — it requires a locked canonical reference sheet per character before any story page generation begins. This is not optional: diffusion models produce measurable visual drift without it, and readers notice immediately in a printed children's book.

The key risks are: (1) Flux Kontext character drift and multi-character confusion — mitigated by stitched reference images and exact prompt token locking; (2) Korean text silently rendering as blank in WeasyPrint — mitigated by bundled `@font-face` Noto KR fonts and a preflight render check; (3) WeasyPrint bleed clipping at page boundary — mitigated by sized HTML elements with negative margins rather than CSS page backgrounds; and (4) KDP rejection for crop marks — mitigated by `marks: none` in the KDP PDF variant. All four risks are preventable with known techniques, but all four must be addressed explicitly in the implementation — none are self-resolving.

---

## Key Findings

### Recommended Stack

The stack is well-determined with high confidence across all categories. Typer 0.24.1 + Rich 14.3.3 handle the CLI layer. The Anthropic SDK 0.86.0 drives story generation via Claude Sonnet 4.5. The Replicate SDK 1.0.7 drives image generation via Flux Kontext Pro, with a provider-agnostic `ImageProvider` ABC enabling future swapping. WeasyPrint 68.1 handles HTML-to-PDF rendering; pikepdf 10.5.1 post-processes print PDFs to embed sRGB ICC profiles and correct PDF box geometry. Pydantic v2.12.5 validates all YAML config at load time, and ruamel.yaml 0.19.1 (not PyYAML) preserves comments in round-tripped style guide files.

The only moderate-confidence stack element is the WeasyPrint + pikepdf two-pass PDF approach — the integration is custom code, not a pre-built solution. The Flux Kontext 90-95% character fidelity claim comes from a single vendor source and requires empirical validation early.

**Core technologies:**
- Typer 0.24.1: CLI framework — Click with type hints, less boilerplate, Rich integration
- anthropic 0.86.0: Story generation — first-party SDK, streaming, structured output
- replicate 1.0.7: Image generation — Flux Kontext Pro via stable 1.0 SDK, async predictions
- WeasyPrint 68.1: HTML-to-PDF — pure Python, CSS `@page` bleed support, no browser dependency
- pikepdf 10.5.1: PDF post-processing — ICC OutputIntent embedding, MediaBox/TrimBox/BleedBox correction
- Pydantic 2.12.5: Config validation — type-safe errors at load time, not mid-pipeline
- ruamel.yaml 0.19.1: Style guide YAML — preserves human-edited comments on round-trip
- Jinja2 3.1.6: HTML templating — one template with edition parameter, not three separate files

### Expected Features

The pipeline must produce bilingual (English + Korean) PDFs in three editions (English-only, Korean-only, Bilingual) in two format variants each (screen for Gumroad, print for KDP). Character consistency across 20 pages is the single most important quality signal. KDP compliance (300 DPI, 0.125" bleed, no crop marks, sRGB ICC, AI disclosure) is non-negotiable for distribution. Human review gates before illustration and before publishing protect both quality and budget.

See `.planning/research/FEATURES.md` for full feature table with complexity ratings.

**Must have (table stakes):**
- Story markdown → rendered bilingual PDF in all three editions
- Consistent character appearance across all pages via Flux Kontext reference images
- 300 DPI image output (2625×2625px minimum for 8.5×8.5" with bleed)
- Bleed-ready print PDF (0.125" per edge, no crop marks, sRGB ICC profile)
- Human review gate before illustration (story approved) and before publish (PDF approved)
- Skip/resume completed images — state tracked per page in JSON
- AI content disclosure flag in publish checklist (KDP policy requirement)

**Should have (differentiators):**
- YAML style guide as single source of truth for art direction across books
- Provider-agnostic image interface (Replicate today, others via config swap)
- Three edition outputs from one story source (triples distribution surface)
- Publish package generation with Claude-generated listing copy for Gumroad and KDP
- `--redo PAGE` flag for selective page regeneration without touching the rest
- Content calendar with holiday backplanning (`calendar` command)
- Image generation cost tracking per run

**Defer (v2+):**
- Web GUI / dashboard
- Automated Gumroad or KDP upload (no public APIs exist)
- ePub/MOBI output
- CMYK PDF (WeasyPrint cannot produce it; KDP converts sRGB internally)
- Audio pronunciation tracks
- LoRA/fine-tuning per series (use Flux Kontext reference images first; add LoRA if that proves insufficient)

### Architecture Approach

BookForge is a linear stage pipeline with human review gates. Each command reads from the previous stage's output in the per-project directory and writes state atomically to `state.json`. The CLI layer (Typer) contains zero business logic — it dispatches to service modules. The architecture separates into 8 components: CLI, State, Story, Image, StyleGuide, Build, Publish, and Calendar. The Image layer uses an `ImageProvider` ABC with concrete adapters, making the provider swappable via `style_guide.yaml` config rather than code changes.

See `.planning/research/ARCHITECTURE.md` for the full component diagram, state schema, data flow, and directory structure.

**Major components:**
1. CLI Layer (`bookforge/cli/`) — command parsing, review gates, progress output; no business logic
2. Project State (`bookforge/state.py`) — atomic JSON read/write tracking stage completion and per-page image status
3. Story Layer (`bookforge/story/`) — parse story.md into `Book` dataclass; generate via Claude; validate bilingual completeness
4. Image Layer (`bookforge/images/`) — provider-agnostic generation with Flux Kontext; resume/retry logic keyed on state
5. Style Guide (`bookforge/style/`) — load/validate YAML; single source of truth for prompts, dimensions, character refs
6. Build Layer (`bookforge/build/`) — Jinja2 HTML assembly; WeasyPrint PDF export; pikepdf print post-processing
7. Publish Layer (`bookforge/publish/`) — bundle PDFs + Claude-generated listing copy + upload checklist
8. Calendar Layer (`bookforge/calendar/`) — holiday YAML + date arithmetic; Rich table output; no external dependencies

### Critical Pitfalls

1. **Character identity drift across 20+ pages** — Lock canonical reference sheet images per character before any story page generation. Always pass reference images as input; never chain from prior page output (drift accumulates). Use exact identical prompt tokens for character descriptions across all pages.

2. **Flux Kontext multi-character confusion** — When both Ho-rang and Gom-i appear together, stitch their reference images into a single combined input (not two separate calls). Black Forest Labs explicitly recommends this. Budget 2-3x generation retries for multi-character pages.

3. **Korean text silently blank in WeasyPrint** — Use `@font-face url()` with bundled Noto Sans KR font files. Never rely on `local()` system font matching. Add a pipeline preflight check that renders a test Korean character and validates glyph coverage in the output PDF before running the full book.

4. **WeasyPrint bleed clips at page boundary** — Use sized HTML elements with negative margins pushed into the bleed zone, not CSS backgrounds on `@page`. This is a known open WeasyPrint bug (#934) that is not fixed by CSS alone.

5. **KDP rejects PDFs with crop marks** — The print PDF variant must use `marks: none` in CSS. Crop marks are fine for a personal proofing variant but cause KDP submission rejection. The `publish` command must validate this before packaging.

---

## Implications for Roadmap

Research reveals clear build-order dependencies. The pipeline is sequential: state management enables all other layers; story parsing enables illustration; illustration enables layout; layout enables PDF; PDF enables publishing. The image generation phase carries the highest technical risk and must be validated early before the rest of the pipeline is built on top of it.

### Phase 1: Foundation and Story Pipeline

**Rationale:** Everything downstream depends on the `Book` dataclass and `state.json`. Building these first — with a working `bookforge new` and story parser — means every subsequent phase can be tested against real data (the Dangun POC story) from day one. Story generation via Claude is well-understood and relatively low-risk.

**Delivers:** Working `bookforge new`, `bookforge story`, and human review gate. Parseable `Book` dataclass from the POC story file. Validated style guide loader.

**Addresses:** Story markdown format, bilingual validation, review gate (table stakes)

**Avoids:** Business logic in CLI layer (anti-pattern); state in memory across commands (anti-pattern)

**Components:** `state.py`, `story/schema.py`, `story/parser.py`, `story/generator.py`, `story/validator.py`, `style/loader.py`, `cli/new.py`, `cli/story.py`

### Phase 2: Image Generation (Highest Risk — Validate Early)

**Rationale:** Flux Kontext character consistency is the central technical gamble. If reference-image conditioning doesn't produce acceptable results, the mitigation (LoRA fine-tuning) significantly changes the cost model and pipeline design. This must be discovered and resolved before building the PDF layer on top. Implement state file and resume logic here before any API calls to prevent wasted spend.

**Delivers:** Working `bookforge illustrate` with Flux Kontext Pro via Replicate, async polling with progress output, per-page state tracking, skip/resume on re-run, `--redo PAGE` flag, cost tracking.

**Addresses:** Character consistency (table stakes), skip/resume (table stakes), retry on failure (table stakes), cost tracking (differentiator)

**Avoids:** Pitfalls 1 (drift), 2 (multi-character), 8 (cold start hangs), 13 (non-idempotent state), 14 (timeout)

**Components:** `images/provider.py`, `images/providers/flux_kontext.py`, `images/service.py`, `cli/illustrate.py`

**Research flag:** Needs empirical validation of Flux Kontext character fidelity on actual Ho-rang and Gom-i reference images before treating as complete. Run 3-5 test pages, evaluate consistency, decide if LoRA is needed before proceeding.

### Phase 3: Layout and PDF Build

**Rationale:** Once images are validated, the build layer can be constructed. The WeasyPrint bleed and Korean font issues must be resolved before building the full pipeline, or they silently corrupt every book. Build a single-page reference test for bleed and Korean rendering before assembling the full book layout.

**Delivers:** Working `bookforge build` producing all 6 PDF variants (3 editions × screen/print). KDP-compliant print PDFs with correct bleed, no crop marks, sRGB ICC profile, and 300 DPI validation. Korean text rendering correctly with bundled Noto KR font.

**Addresses:** Bilingual layout (table stakes), three editions (differentiator), print PDF (table stakes), screen PDF (table stakes)

**Avoids:** Pitfalls 3 (Korean blank), 4 (CJK font slowdown), 5 (bleed clipping), 10 (language hierarchy), 11 (wrong DPI), 12 (crop marks)

**Components:** `build/assembler.py`, `build/exporter.py`, `build/templates/`, `build/css/`, `cli/build.py`

**Research flag:** WeasyPrint + pikepdf two-pass integration for print PDF is custom code. Validate print PDF compliance via KDP's online previewer before treating Phase 3 as done.

### Phase 4: Publish Package and Review Gate

**Rationale:** The publish layer is a packaging concern that depends on completed PDFs. It's deliberately thin (no API uploads exist) but the listing copy generation and upload checklist add meaningful value with low complexity. The review gate command finalizes the approval workflow.

**Delivers:** Working `bookforge review` (opens PDF in browser, prompts approval) and `bookforge publish` (generates zipped package with PDFs, Gumroad listing, KDP listing, and UPLOAD-CHECKLIST.md including AI disclosure reminder).

**Addresses:** Publish package (differentiator), listing copy generation (differentiator), AI disclosure flag (table stakes)

**Avoids:** Pitfalls 6 (spine width wrong), 7 (AI disclosure skipped), 16 (wrong edition uploaded)

**Components:** `publish/packager.py`, `publish/listing.py`, `cli/publish.py`, `cli/review.py`

### Phase 5: Resilience and Calendar

**Rationale:** Retry/resume hardening and cost tracking make the pipeline production-ready for the 1-book/month cadence. The calendar command is genuinely useful for scheduling but has zero dependencies on any other component — build it last.

**Delivers:** Hardened exponential backoff on image generation failures, comprehensive cost reporting per run, `bookforge calendar` with holiday-driven deadline backplanning.

**Addresses:** Retry on failure (table stakes), cost tracking (differentiator), content calendar (differentiator)

**Avoids:** Pitfall 9 (style inconsistency across sessions — pin model version hash in state)

**Components:** Enhancements to `images/service.py`; `calendar/service.py`, `calendar/holidays.yaml`, `cli/calendar.py`

### Phase 6: Additional Image Providers (If Needed)

**Rationale:** Only build if Phase 2 reveals that Flux Kontext Pro is insufficient or too expensive. The `ImageProvider` ABC already supports this; it's just adding concrete adapters.

**Delivers:** `flux_dev.py` (cheaper) and `dalle3.py` (fallback, no character refs) provider adapters.

**Conditional on:** Phase 2 empirical validation results.

### Phase Ordering Rationale

- State and schema must come first — they are imported by every other layer.
- Image generation before layout — character consistency is the highest technical risk; discovering it's insufficient after building the PDF layer wastes effort.
- Build layer after images — requires validated image files to test against.
- Publish after build — pure packaging step, no value without PDFs to package.
- Calendar last — fully independent, simplest to defer without blocking anything.
- This ordering matches the architecture's own suggested build order and mirrors the natural production workflow.

### Research Flags

Phases needing deeper research or empirical validation:
- **Phase 2:** Flux Kontext character fidelity needs hands-on testing with actual Ho-rang and Gom-i reference images. The 90-95% fidelity claim is from a single vendor source. Run a 3-5 page spike before building resume/cost/retry infrastructure.
- **Phase 3:** WeasyPrint + pikepdf two-pass print PDF is custom integration. The individual pieces are documented; the composition is not. Build a reference single-page bleed test before full book rendering.

Phases with standard patterns (skip research-phase):
- **Phase 1:** Story generation via Claude API and markdown parsing are well-documented. Pydantic v2 + python-frontmatter patterns are standard. No surprises expected.
- **Phase 4:** Publish packaging is file I/O + Claude API call. Extremely well-trodden territory.
- **Phase 5:** Calendar is pure date math + YAML. No external dependencies, no risk.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All versions PyPI-verified 2026-03-24; major alternatives considered and rejected with rationale |
| Features | HIGH | KDP and Gumroad specs from official documentation; bilingual typography from peer-reviewed academic sources |
| Architecture | HIGH | Standard Python linear pipeline patterns; well-established Click/Typer command group structure |
| Pitfalls | MEDIUM-HIGH | KDP rejection pitfalls from official docs (HIGH); Flux Kontext behavior from official Black Forest Labs docs + community (MEDIUM); WeasyPrint bugs from verified GitHub issues |

**Overall confidence:** HIGH for plan structure; MEDIUM for Flux Kontext character consistency at scale (requires empirical validation)

### Gaps to Address

- **Flux Kontext fidelity empirical validation:** The 90-95% character consistency figure is unverified for this specific use case (Korean watercolor style, tiger + bear characters). Resolve in Phase 2 spike before building on top. If fidelity is insufficient, the fallback is Replicate LoRA fine-tuning (~$1.85/run).
- **Replicate async API confirmation:** `replicate.async_run()` behavior in SDK 1.0.7 should be confirmed against the changelog before building the concurrency layer. The synchronous `replicate.run()` 60-second timeout is borderline for cold starts.
- **WeasyPrint bleed visual content:** WeasyPrint 68.1 may partially resolve GitHub issue #934 (background clipping at bleed). Verify empirically with an illustration that intentionally bleeds to the edge before committing to the element-with-negative-margins workaround.
- **Korean font embedding on clean environments:** The Noto Sans KR bundling strategy needs validation on a fresh Linux environment without any CJK fonts installed — the most likely failure scenario in CI/CD.

---

## Sources

### Primary (HIGH confidence)
- [KDP Paperback Submission Guidelines](https://kdp.amazon.com/en_US/help/topic/G201857950) — bleed, trim, margin, format requirements
- [KDP Set Trim Size, Bleed, and Margins](https://kdp.amazon.com/en_US/help/topic/GVBQ3CMEQW3W2VL6) — 8.5×8.5" trim, 0.125" bleed, 300 DPI spec
- [KDP Print Options](https://kdp.amazon.com/en_US/help/topic/G201834180) — color options, paper types
- [WeasyPrint official documentation](https://doc.courtbouillon.org/weasyprint/stable/) — CSS bleed/marks support
- [WeasyPrint bleed bug #934](https://github.com/Kozea/WeasyPrint/issues/934) — background clipping limitation
- [WeasyPrint CJK slowdown #2120](https://github.com/Kozea/WeasyPrint/issues/2120) — 6x slowdown with CJK fonts
- [WeasyPrint Korean blank text #2366](https://github.com/Kozea/WeasyPrint/issues/2366) — silent failure without CJK fonts
- [pikepdf ICC OutputIntent #509](https://github.com/pikepdf/pikepdf/issues/509) — ICC embedding confirmed
- [Black Forest Labs FLUX.1 Kontext prompting guide](https://docs.bfl.ml/guides/prompting_guide_kontext_i2i) — multi-character reference image guidance
- [Bilingual typography implications (peer-reviewed)](https://www.tandfonline.com/doi/full/10.1080/1051144X.2023.2168397) — Korean font sizing and line height requirements
- PyPI version verification (2026-03-24): anthropic 0.86.0, replicate 1.0.7, weasyprint 68.1, pikepdf 10.5.1, typer 0.24.1, rich 14.3.3, pydantic 2.12.5

### Secondary (MEDIUM confidence)
- [Together.ai FLUX.1 Kontext blog](https://www.together.ai/blog/flux-1-kontext) — character consistency claims (90-95% fidelity)
- [Replicate consistent characters blog](https://replicate.com/blog/generate-consistent-characters) — Flux Kontext reference image workflow
- [Replicate prediction lifecycle](https://replicate.com/docs/topics/predictions/lifecycle) — async polling pattern
- [KDP AI disclosure rules 2025](https://www.brandonrohrbaugh.com/blog/kdp-ai-disclosure-rules-2025-explained) — AI content policy
- [KDP cover rejection checklist 2026](https://bookcoverslab.com/guides/kdp-cover-rejection-checklist-2026) — spine width calculation

### Tertiary (LOW confidence)
- [Character consistency in AI art 2026](https://aistorybook.app/blog/ai-image-generation/character-consistency-in-ai-art-solved) — general landscape, single source
- [Childbook.ai](https://www.childbook.ai/) — competitor, used for anti-feature signals only

---
*Research completed: 2026-03-24*
*Ready for roadmap: yes*
