# Feature Landscape

**Domain:** AI-assisted children's book production pipeline (CLI tool)
**Project:** BookForge — Bilingual Korean Children's Book Pipeline
**Researched:** 2026-03-24
**Confidence:** MEDIUM-HIGH (KDP/Gumroad specs verified via official sources; AI consistency patterns from multiple corroborating sources)

---

## Table Stakes

Features users expect. Missing = product feels broken or unusable.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Story file → rendered book | Core pipeline promise; without this nothing works | High | Markdown in, PDF out |
| Consistent character appearance across pages | Single biggest quality signal for children's books; readers immediately notice drift | High | Hardest technical problem in the domain; see Pitfalls |
| 300 DPI image output | KDP hard requirement; below 300 DPI = rejected or visibly pixelated in print | Medium | 2550×2550px for full-page 8.5x8.5 |
| Bleed-ready print PDF (0.125" per edge) | KDP requires it for any full-bleed illustration; missing = print submission failure | Medium | Entire file must be set to bleed if any single page uses bleed |
| Safe zone / margin compliance (0.25"+ inside trim) | Text and key art inside trim line; violating this causes text getting cut off in print | Low | CSS @page margin rules |
| Bilingual text on page | The product's core value proposition | Medium | English + Korean on same page spread |
| Human review gate before irreversible steps | Illustration costs real money; illustration without story sign-off wastes budget | Low | Prompt before generate, prompt before publish |
| Skip/resume completed images | Image generation costs $0.03–0.055/image; re-generating finished pages is wasteful | Medium | Track state in sidecar file or directory convention |
| PDF export for digital download (screen, RGB) | Gumroad distribution requires a clean digital PDF | Low | No bleed, sRGB, smaller file |
| Retry failed images | Network errors and API timeouts are normal; pipeline must not die on one failure | Low | Exponential backoff, isolated per-page |
| AI content disclosure flag | KDP policy: must disclose AI-generated illustrations during upload; non-disclosure = account penalty | Low | Generate flag in publish package output |

---

## Differentiators

Features that set this product apart. Not expected from the domain, but deliver meaningful value.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| YAML style guide system | Single source of truth for art direction; makes prompt authoring consistent without repeating style prose on every page | Medium | Character descriptions, color palette, art style prefix all centrally versioned |
| Provider-agnostic image interface | Not locked to Replicate/Flux; swap to OpenAI, Stability AI, or local ComfyUI via config | Medium | Abstracts API calls behind a common `ImageProvider` protocol |
| Character reference image injection (Flux Kontext) | IP-Adapter / Kontext reference images dramatically improve cross-page character consistency vs. prompt-only approaches | High | Requires maintaining canonical "seed" images for Ho-rang and Gom-i; Kontext preserves character embedding without fine-tuning |
| Three edition outputs from one source | English-only, Korean-only, and bilingual from a single story file; triples distribution surface | Medium | Layout engine must render each edition without manual work |
| Holiday-driven content calendar | Automated release date backplanning (publish 2-3 weeks before holiday) removes scheduling cognitive load | Low | Simple date math from YAML calendar config; Korean + US holidays |
| Publish package generation | Produces upload-ready bundle (PDFs + listing copy) for manual Gumroad/KDP submission; bridges the "no public API" gap | Low | Structured output dir; pre-written description, tags, pricing suggestion |
| Story markdown format with per-page image prompts | Collocates narrative text and illustration direction; removes separate prompt spreadsheet overhead | Low | YAML frontmatter + page boundary markers + bilingual blocks |
| `--redo` flag for selective page regeneration | Lets you re-illustrate a specific page without touching the rest; enables iterative art direction | Low | Keyed on page number or identifier |
| Image generation cost tracking | Shows per-book spend during `illustrate` step; surfaces budget overruns before they accumulate | Low | Log cost per call; print running total |
| Listing copy generation (Claude) | Produces Gumroad/KDP product description, keywords, categories in the correct character limits | Medium | Derived from story frontmatter + style guide |

---

## Anti-Features

Features to explicitly NOT build in v1.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Web dashboard / GUI editor | 1 book/month workflow doesn't justify UI build cost; adds maintenance burden with no user-facing benefit | CLI is sufficient; add GUI only if production reaches 5+ books/month or handoff to non-technical user |
| Automated Gumroad product creation | Gumroad has no public product-creation API; scraping/unofficial API = ToS risk and fragility | Generate publish package for manual upload |
| Automated KDP upload | No KDP product-creation API exists; automation would require brittle browser automation | Generate print-ready PDFs + listing copy for manual KDP submission |
| ePub / MOBI output | No demand signal; children's picture books are not well-served by reflowable ePub | PDF only; revisit if ebook readers become primary channel |
| CMYK PDF output | WeasyPrint cannot produce CMYK; KDP converts sRGB internally and the result is acceptable for print | sRGB ICC profile embedded in print PDF; document this limitation explicitly |
| Audio pronunciation tracks | Valuable feature but significantly increases production complexity (recording, sync, hosting) | Defer until catalog is established and demand is proven |
| Social media asset automation | Out of scope for book production; separate concern | Defer; generate static cover art export that can feed social manually |
| IngramSpark distribution | More complex distribution setup; add only when KDP demand is proven | Start with KDP + Gumroad; revisit at 10+ titles |
| AI fine-tuning / LoRA training | Per-project LoRA training would give highest consistency but costs $1.85+ per training run and adds pipeline complexity | Use Flux Kontext reference-image approach; fine-tune only if reference images prove insufficient after several books |
| Real-time collaboration / sharing | Single-creator tool; no multi-user workflow needed | N/A |
| Book series management database | Overkill for 1 book/month cadence; filesystem + git is sufficient | Use directory conventions and YAML frontmatter for series metadata |

---

## Feature Dependencies

```
style_guide (YAML) → illustrate (image generation)
    └─ character reference images → image generation consistency

story (Markdown) → review gate (human proofreads Korean)
    └─ review gate approval → illustrate
        └─ illustrate → build (PDF assembly)
            └─ build → review gate (final review)
                └─ final review → publish package generation
                    └─ publish package → manual Gumroad/KDP upload

three editions → build
    └─ build (English-only)
    └─ build (Korean-only)
    └─ build (Bilingual)
    each edition → screen PDF (Gumroad) + print PDF (KDP)

content calendar → new (story scaffolding)
    └─ calendar config (holidays) → release date → backplanned milestones

image retry/resume → illustrate
    └─ state tracking (completed pages) → skip logic
    └─ --redo flag → force specific pages
```

---

## MVP Recommendation

**Phase 1 — Minimum viable book production:**
1. Story markdown format (YAML frontmatter + page blocks + bilingual text + image prompts)
2. `illustrate` command with Flux Kontext via Replicate (character reference image support)
3. Style guide YAML (art style prefix, character descriptions, color palette)
4. `build` command with WeasyPrint (bilingual layout, three editions, screen PDF)
5. Human review gates (`review` command — approve/reject story and final PDF)

**Phase 2 — Print distribution:**
6. Print PDF output (bleed, trim marks, 300 DPI, sRGB ICC profile, KDP page count compliance)
7. Publish package generation (structured output dir + listing copy via Claude)
8. AI content disclosure flag in publish package

**Phase 3 — Resilience and calendar:**
9. Image retry/resume (skip completed, exponential backoff, `--redo` flag)
10. Cost tracking per image generation run
11. Content calendar (`calendar` command with holiday scheduling)

**Defer indefinitely:**
- Web GUI, automated uploads, ePub, CMYK, audio, social media automation

---

## Feature Detail Notes

### AI Image Consistency (Critical Path)

The character consistency problem is the central technical challenge. Modern (2025-2026) approaches ranked by effectiveness:

1. **Flux Kontext reference-image conditioning** (recommended) — In-context image editing preserves character identity across scenes without fine-tuning. Black Forest Labs' approach embeds a mathematical fingerprint from 1-3 reference images. Best for recurring characters like Ho-rang and Gom-i.
2. **IP-Adapter with FLUX.1-dev** — Separate style and character reference images; more control but higher prompt engineering overhead.
3. **LoRA fine-tuning on Replicate** — Highest fidelity but costs ~$1.85 per training run and requires curated training images. Overkill for initial series.
4. **Prompt-only with strong character description prefix** — Lowest cost but least reliable; acceptable only for background/scene images.

The style guide YAML must encode the character description as a reusable prompt prefix injected into every page prompt. The canonical seed images for each character should be stored in the repo and referenced on every generation call.

### Bilingual Layout Conventions

Korean/English bilingual children's books use one of three visual hierarchy strategies:
1. **Primary/secondary** — One language at full size, other in smaller type below (common for heritage language books where English is assumed dominant)
2. **Side-by-side** — Languages in parallel columns or facing pages (suits older readers)
3. **Visual parity** — Both languages at equal weight, differentiated by color or font family (recommended for Ho-rang & Gom-i series targeting ages 4-8)

Key typographic constraints for Korean:
- Korean characters (Hangul) require a significantly larger minimum font size than Latin to remain legible for young readers — minimum 14pt for body text, 18pt+ preferred
- Korean line height should be ~1.6× the font size (wider than English 1.4×) due to character density
- Avoid decorative Latin fonts for Korean text; use a clean, rounded Korean typeface (Noto Sans KR, Nanum Gothic, or similar) that harmonizes with the "Korean Cute Watercolor" aesthetic

### KDP Print PDF Specifications (8.5×8.5, Full Color)

Verified against official KDP documentation:
- **Trim size:** 8.5" × 8.5" (most popular KDP picture book format)
- **Bleed:** 0.125" (3.2mm) on top, bottom, and outside edges; entire file must be in bleed mode if any page uses bleed
- **Safe zone:** Content 0.25"–0.375" inside trim line
- **Image resolution:** 300 DPI minimum; full-page spread at 8.75×8.75" (with bleed) = 2625×2625px
- **Color:** sRGB (KDP converts internally; CMYK not required)
- **File format:** Print-ready PDF (required for bleed books)
- **File size limit:** 650 MB
- **Color ink option:** Premium color (required for full-color picture books in hardcover)
- **AI disclosure:** Required during KDP upload; confidential between publisher and Amazon; does not affect customer-facing visibility

### Gumroad Digital PDF Specifications

- **Format:** PDF (drag-and-drop upload, up to 16 GB)
- **Color space:** sRGB (screen-optimized)
- **No bleed/trim marks required**
- **Fee:** 10% flat on every sale; no monthly fee
- **Delivery:** Secure download link emailed to buyer immediately after purchase
- **Multiple file variants:** Can bundle English, Korean, and Bilingual editions as separate files or a single ZIP

### Content Calendar Feature Scope

For a 1-book/month cadence, the calendar feature should be deliberately minimal:
- YAML config listing target holidays with release dates
- Backplan computation: release date minus 2-3 weeks = publish date; publish date minus N days per production step = step deadlines
- `calendar` command outputs a human-readable schedule for the next N months
- No database, no project management integration; text output only

Anti-scope: Do not build a task management system. The calendar surfaces dates; a human tracks tasks.

---

## Sources

- [KDP Paperback Submission Guidelines](https://kdp.amazon.com/en_US/help/topic/G201857950) — official, HIGH confidence
- [KDP Set Trim Size, Bleed, and Margins](https://kdp.amazon.com/en_US/help/topic/GVBQ3CMEQW3W2VL6) — official, HIGH confidence
- [KDP Print Options](https://kdp.amazon.com/en_US/help/topic/G201834180) — official, HIGH confidence
- [Best Children's Book Sizes for Amazon KDP (2026)](https://www.neolemon.com/blog/best-childrens-book-sizes-for-amazon-kdp/) — MEDIUM confidence
- [Will Amazon KDP Accept AI-Illustrated Children's Books?](https://www.neolemon.com/blog/will-amazon-kdp-accept-ai-illustrated-childrens-books/) — MEDIUM confidence
- [KDP AI Disclosure Rules for 2025 Explained](https://www.brandonrohrbaugh.com/blog/kdp-ai-disclosure-rules-2025-explained) — MEDIUM confidence
- [Amazon KDP AI Disclosure Policy 2026](https://www.inkfluenceai.com/blog/amazon-kdp-ai-disclosure-policy-2026) — MEDIUM confidence
- [FLUX.1 Kontext — Together AI blog](https://www.together.ai/blog/flux-1-kontext) — MEDIUM confidence
- [Character Consistency in AI Art: The 2026 Breakthrough](https://aistorybook.app/blog/ai-image-generation/character-consistency-in-ai-art-solved) — LOW confidence (single source)
- [Best AI for Character Consistency in 2026](https://toonystory.com/blog/best-ai-for-character-consistency-2026) — LOW confidence (single source)
- [WeasyPrint official documentation](https://doc.courtbouillon.org/weasyprint/stable/) — HIGH confidence
- [WeasyPrint Bleed & Page Backgrounds issue #934](https://github.com/Kozea/WeasyPrint/issues/934) — MEDIUM confidence
- [Implications of typographic design in bilingual picturebooks](https://www.tandfonline.com/doi/full/10.1080/1051144X.2023.2168397) — HIGH confidence (peer-reviewed)
- [How to Self-Publish a Bilingual Children's Book — IngramSpark](https://www.ingramspark.com/blog/how-to-self-publish-a-bilingual-childrens-book) — MEDIUM confidence
- [Selling Ebooks on Gumroad](https://www.topbubbleindex.com/blog/selling-ebooks-gumroad/) — MEDIUM confidence
- [Designing Bilingual Books for Children (ResearchGate)](https://www.researchgate.net/publication/274370569_Designing_Bilingual_Books_for_Children) — HIGH confidence (academic)
- [Replicate FLUX collections](https://replicate.com/collections/flux) — MEDIUM confidence
- [Childbook.ai](https://www.childbook.ai/) — LOW confidence (competitor, marketing claims)
