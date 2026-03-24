# Domain Pitfalls

**Domain:** AI-illustrated bilingual children's book production pipeline (Python CLI)
**Researched:** 2026-03-24
**Confidence:** MEDIUM-HIGH (most findings verified across multiple sources; Flux Kontext behavior from official docs + community)

---

## Critical Pitfalls

Mistakes that cause rewrites, KDP rejections, or broken production output.

---

### Pitfall 1: Character Identity Drift Across 20+ Pages

**What goes wrong:** Ho-rang and Gom-i look visibly different from page to page — fur color lightens, eye shape shifts, proportions change. Each Flux generation is independent; there is no built-in memory linking page 2 to page 14.

**Why it happens:** Diffusion models sample from probability distributions. Even identical prompts with the same reference image will produce small variations. Over 20 pages those variations compound. Flux Kontext multi-turn editing reduces drift compared to alternatives, but the official technical paper still documents measurable drift during iterative workflows.

**Consequences:** A printed proof where characters are unrecognizable across pages. Readers notice immediately. A professional-looking product becomes amateur.

**Prevention:**
- Build and lock a canonical "character reference sheet" image for each mascot before generating any story pages. This sheet should show the character in the target style from multiple angles. Store it in the style guide and always pass it as the reference input.
- When using Flux Kontext image-to-image mode, maintain a single "source of truth" image per character rather than re-generating fresh on every page. Chain edits from the reference, not from the prior page output (chaining accumulates drift).
- When multiple characters appear together, stitch reference images into a single combined image before passing as the reference — Flux's multi-subject input is most reliable this way. Do NOT send them as separate reference calls.
- Track reference image filenames and hashes in the pipeline state so `--redo` regenerations always use the same reference.
- Prompt tokens must be identical for character-describing terms across all pages (e.g., always "Ho-rang the tiger, orange fur with black stripes, round friendly eyes" — never paraphrase).

**Detection:** Visual QA: open all page images in a grid view before proceeding to layout. The `review` command should display a contact sheet of all pages.

**Phase:** Illustration pipeline (Phase 2/3) — establish reference sheet workflow before any story page generation.

---

### Pitfall 2: Flux Kontext Multi-Character Confusion

**What goes wrong:** When both Ho-rang and Gom-i appear in the same scene, the model frequently blends their features — one character may inherit the other's color or lose a defining trait. Reported by Flux Kontext users: "when inputting multiple characters, it sometimes loses one or two characters."

**Why it happens:** The model's cross-attention mechanism conflates features from multiple reference inputs when they share visual space in the prompt.

**Consequences:** Pages that should show both mascots together have one character looking wrong. These are likely the most narratively important pages in the book.

**Prevention:**
- Stitch Ho-rang and Gom-i reference images side-by-side into a single combined reference image (not passed as two separate inputs). Black Forest Labs documentation explicitly recommends this for multi-character scenes.
- For scenes where one character is less prominent, describe the foreground character more verbosely in the prompt and the background character more briefly.
- Budget extra generation retries (2-3x) for multi-character pages in the cost model.

**Detection:** Any page prompt containing both character names should be flagged in the pipeline as "multi-character — verify manually."

**Phase:** Style guide design (Phase 1); illustration pipeline (Phase 2/3).

---

### Pitfall 3: Korean Text Rendering to Silent Blank in WeasyPrint

**What goes wrong:** WeasyPrint generates a PDF with no visible Korean characters — blank white spaces where the Korean text should appear. No error is raised. The PDF looks valid but is empty of Korean content.

**Why it happens:** WeasyPrint uses system fonts. If the deployment environment (or the developer's machine) does not have a Korean/CJK font installed, the text renders as blank rather than falling back to tofu boxes or raising an exception. This is documented in WeasyPrint issue #2366 and confirmed across multiple community reports.

**Consequences:** You upload a KDP book where all Korean text is invisible. This would not be caught until proof review or customer complaint.

**Prevention:**
- Explicitly embed a Korean-capable font (Noto Sans KR or Noto Serif KR) via CSS `@font-face` using `url()` paths pointing to local font files — never rely on `local()` name matching, which fails silently across environments.
- Bundle the font files inside the project repository or as a required dependency. Do not rely on system font installation.
- Add a pipeline preflight check that renders a single test character (e.g., "안") and validates the output PDF has non-zero glyph coverage for Korean Unicode range before running the full book.

**Detection:** Include a CI/preflight step that opens the generated PDF and checks for Korean character presence. Even a simple file size check (a page with blank text is measurably smaller) provides a signal.

**Phase:** Layout/PDF engine setup (Phase 2) — must be verified before any bilingual layout work begins.

---

### Pitfall 4: CJK Font Causes 6x PDF Generation Slowdown

**What goes wrong:** Switching from Latin to CJK fonts in WeasyPrint dramatically increases PDF generation time — documented at ~6x slower. A book that takes 5 seconds to render becomes 30+ seconds. In a pipeline running 20+ pages this compounds.

**Why it happens:** WeasyPrint's "Step 7 - Adding PDF metadata" bloats with full CJK font subsetting — Noto Sans CJK contains thousands of glyphs, all of which get processed even if only a few dozen are used.

**Consequences:** Slow build command UX; timeout issues if running in CI.

**Prevention:**
- Use a Korean-only weight of Noto (e.g., `NotoSansKR-Regular.otf`) rather than the pan-CJK variant (`Noto Sans CJK TC`) to limit glyph set.
- Consider font subsetting as a build step: use `pyftsubset` to generate a custom font file containing only the Unicode characters actually used in the book, then reference that subset in CSS.

**Detection:** Time the `build` command. If Korean edition takes >3x longer than English edition, CJK font bloat is the cause.

**Phase:** Layout engine optimization (Phase 2 / performance pass).

---

### Pitfall 5: WeasyPrint Bleed Not Working as Expected

**What goes wrong:** Full-bleed backgrounds (page-filling illustrations) are clipped at the `@page` boundary. The bleed area outside the trim box remains white. This is a known open issue in WeasyPrint (GitHub issue #934).

**Why it happens:** WeasyPrint clips the background at `@page` dimensions by design in some versions. The CSS `bleed` and `marks` properties were added in v0.41 but page background extension into the bleed area has a separate implementation gap.

**Consequences:** Print PDFs submitted to KDP show white hairline borders at page edges after trimming, making pages look unprofessional. KDP does not reject these — it just prints them badly.

**Prevention:**
- Use a `<div>` or `<img>` element that is explicitly sized to `(trim + bleed)` dimensions with negative margins to push it into the bleed zone, rather than relying on CSS backgrounds on `@page`.
- Set element dimensions to `(8.5 + 0.25) inches` wide × `(8.5 + 0.25) inches` tall for the illustration container (adding 0.125" bleed on each side).
- Validate the bleed area visually in every print PDF before submission using a PDF viewer that shows bleed marks (PDF Expert, Acrobat).

**Detection:** Open print PDF in Acrobat, enable "Show Art/Trim/Bleed Boxes." Any white showing between the trim box and bleed box means bleed is not extending correctly.

**Phase:** Print PDF template implementation (Phase 2-3). Build a reference single-page test before the full pipeline.

---

### Pitfall 6: KDP Cover Spine Width Recalculated on Every Interior Change

**What goes wrong:** The cover spine width is calculated from `page_count × paper_thickness`. If the interior page count changes by even 2 pages (adding a dedication page, copyright page, etc.) and the cover file is not regenerated, KDP rejects the submission.

**Why it happens:** KDP's review system validates cover dimensions against the uploaded interior. Off by a fraction of an inch — rejected without clear explanation.

**Consequences:** Rejected submission, delay to publish date, regenerating and re-uploading cover.

**Specifics:**
- White paper: 0.002252" per page
- Cream paper: 0.0025" per page
- Color paper: 0.0032" per page
- Books under 79 pages: spine text is prohibited by KDP; text on a thin spine triggers rejection

**Prevention:**
- The `publish` command must calculate and embed the correct spine width at submission time, not at design time.
- Treat cover generation as a pipeline step that depends on `page_count` as an input parameter.
- Always use KDP's cover calculator (or replicate its formula exactly in code) — do not hardcode a spine width.
- Lock the paper type in config (`white` for this project) and assert it never changes without a cover rebuild.

**Detection:** The `publish` command should calculate expected spine width and compare against the submitted cover file's actual dimensions before generating the package.

**Phase:** Cover generation and publish command (Phase 3-4).

---

### Pitfall 7: KDP Mandatory AI Content Disclosure

**What goes wrong:** Failing to disclose AI-generated images during KDP submission (the question appears during book setup) results in account penalties or book removal — even if the book was not rejected initially. KDP has stated non-disclosure can lead to account suspension.

**Why it happens:** As of 2025, KDP requires disclosure of AI-generated text AND images. The disclosure is not shown to customers publicly but is required for internal policy compliance. The question appears in the setup flow and many first-time publishers skip or misread it.

**Consequences:** Book removed post-publish, potential account ban. Reputational risk if flagged.

**Prevention:**
- The `publish` command output package checklist must include a reminder: "KDP will ask if your book contains AI-generated content — answer YES for illustrations."
- The distinction: AI-Generated = disclose (this project). AI-Assisted = no disclosure required. This project generates images with Flux = AI-generated.
- Note: IngramSpark currently prohibits AI-generated content entirely. This project is KDP-only for AI illustrations, which is correct per the PROJECT.md out-of-scope decision.

**Detection:** Checklist item in publish package documentation.

**Phase:** Publish workflow (Phase 4+).

---

### Pitfall 8: Replicate Cold Starts Making CLI Feel Broken

**What goes wrong:** Running `bookforge illustrate` hangs for 10-30 seconds with no output before the first image starts generating. Users (including the developer) assume the command crashed or the API key is wrong.

**Why it happens:** Replicate boots model containers on demand. Cold starts for Flux models can take 30+ seconds when the container is not warm. The default `replicate.run()` timeout is 60 seconds — borderline for cold starts on slow queues.

**Consequences:** False sense of bugs; premature Ctrl+C interrupts that could corrupt partial pipeline state.

**Prevention:**
- Show a progress indicator immediately on API call: "Warming up Flux model..." with elapsed time.
- Use Replicate's async prediction API with explicit polling and per-poll status messages rather than blocking on `replicate.run()`. This allows better UX and more control over timeouts.
- Implement the pipeline state file (in-progress JSON) before the first API call, so a Ctrl+C mid-generation can be resumed with `--resume` rather than starting over.
- Set `wait=False` on `replicate.run()` and poll explicitly with status updates every 5 seconds.

**Detection:** Manual testing with a cold model — run the illustrate command after 30+ minutes of inactivity and observe startup behavior.

**Phase:** Illustration command implementation (Phase 2).

---

## Moderate Pitfalls

---

### Pitfall 9: Watercolor Style Inconsistency Across Generation Sessions

**What goes wrong:** Images generated in one session have subtly different color palettes, line weights, or "wetness" of the watercolor effect compared to images generated weeks later. This matters when you need to add pages or regenerate a single page for a book.

**Why it happens:** Flux model weights update on Replicate; the prompt that produced a specific watercolor look in March may produce a slightly different look in May. There is no version pinning on Replicate's hosted models by default.

**Prevention:**
- Pin the Replicate model version string (not just the model name) in the style guide YAML config. Use the specific SHA version hash, not `owner/model:latest`.
- Store the exact model version used alongside each generated image in the pipeline state file.
- The style guide prefix prompt must include explicit color specifications ("ochre, sap green, muted dusty blue, warm cream paper") not vague descriptors ("warm earth tones").

**Detection:** Compare a regenerated page against the originals in a grid view before accepting it.

**Phase:** Style guide design (Phase 1); image generation layer (Phase 2).

---

### Pitfall 10: Language Hierarchy Signal in Bilingual Layout

**What goes wrong:** The bilingual edition accidentally signals that English is the "primary" language through typography choices (larger English text, English always on top, Korean in a different/smaller weight). This is a cultural sensitivity issue for a Korean-American product targeting Korean heritage families.

**Why it happens:** Default CSS hierarchy flows top-to-bottom. English fonts have broader support in most systems. Developers default to familiar choices.

**Consequences:** The product feels dismissive of the Korean language — directly opposite to the brand's cultural mission.

**Prevention:**
- Give English and Korean identical font sizes and weights unless the design spec explicitly calls for differentiation.
- Alternate language order across pages or use a side-by-side layout where neither language dominates.
- Wife's proofread gate must include checking visual parity, not just text accuracy.
- Use Noto Sans KR (not a generic system serif) to give Korean text the same visual richness as English.

**Detection:** Show a bilingual page to a Korean speaker before finalizing the layout template.

**Phase:** Layout template design (Phase 2).

---

### Pitfall 11: Images Generated at Wrong Resolution for Print

**What goes wrong:** Images look fine on screen but print blurry. KDP requires 300 DPI minimum; an 8.5×8.5" page requires `(8.5 + 0.25 bleed on each side) × 300 = 2625px` minimum on the short side.

**Why it happens:** Flux default generation sizes may not match the required print resolution. Developers check screen previews only and never order a physical proof.

**Prevention:**
- Always request images at the target print resolution in the API call. Flux supports up to 1440px or higher depending on model — verify the maximum and upscale if needed.
- For an 8.75" × 8.75" (bleed-extended) page at 300 DPI: minimum `2625 × 2625` px. Request `1024×1024` or higher and upscale with a dedicated upscaler if the model caps below that.
- Add a resolution validation step in the build pipeline: check every image file's pixel dimensions against the required minimum before layout rendering.
- Order one KDP physical proof before the first commercial release.

**Detection:** `bookforge build` should validate image dimensions and warn (or fail) on undersized images.

**Phase:** Image generation pipeline (Phase 2); print PDF validation (Phase 3).

---

### Pitfall 12: PDF Contains Crop Marks — KDP Rejects It

**What goes wrong:** KDP explicitly prohibits crop marks, trim marks, annotations, bookmarks, and invisible objects in submitted PDFs. WeasyPrint's `marks: crop cross` CSS property adds these. Submitting a PDF with crop marks causes rejection.

**Why it happens:** Print professionals expect crop marks. The CSS print spec supports them. But KDP wants them absent — they handle trimming themselves based on the bleed specification.

**Prevention:**
- Do NOT add `marks: crop cross` to the `@page` CSS for KDP submission PDFs.
- A separate "print-for-proofing" PDF variant with marks is fine for personal review, but the KDP submission PDF must have `marks: none`.
- Add a PDF metadata check in the publish package generator to confirm no marks in the output file.

**Detection:** KDP's print previewer will flag the issue — but only after upload. Cheaper to check locally first.

**Phase:** Print PDF template (Phase 2-3).

---

### Pitfall 13: CLI Pipeline State Not Idempotent

**What goes wrong:** Running `bookforge illustrate` twice (e.g., after a crash) regenerates images that already exist, wasting API credits and time. Running it after partial completion replaces good images with new ones.

**Why it happens:** No state file tracking which images have been successfully generated. Each invocation starts from scratch.

**Consequences:** Wasted $10-15 per redundant run; previously good character-consistent images overwritten with inconsistent new ones.

**Prevention:**
- Maintain a pipeline state file (e.g., `.bookforge/state.json` per project) that records: page number, image path, generation timestamp, model version, seed, status.
- Default behavior: skip pages where `status == "complete"` and an image file exists at the recorded path.
- Provide `--redo PAGE_NUM` to regenerate a specific page.
- Provide `--force` to regenerate everything.
- Never overwrite an existing image file unless explicitly asked.

**Detection:** Test by running `bookforge illustrate` twice — second run should complete in seconds with no API calls.

**Phase:** Illustration command (Phase 2) — implement state file before any API integration.

---

## Minor Pitfalls

---

### Pitfall 14: Replicate API Timeout Default Too Short for Cold Starts

**What goes wrong:** The default Replicate Python client timeout is 60 seconds for synchronous predictions. A cold-start Flux container can take 45-55 seconds just to warm up, leaving almost no time for actual inference. The call times out and raises an exception before any image is returned.

**Prevention:** Use async prediction mode (`wait=False`) and poll via the prediction lifecycle endpoint rather than depending on the synchronous timeout.

**Phase:** Illustration command (Phase 2).

---

### Pitfall 15: sRGB ICC Profile Not Embedded in Print PDF

**What goes wrong:** KDP accepts sRGB PDFs but recommends an embedded ICC profile so colors render predictably across their print facilities. Submitting without an ICC profile means colors may shift slightly between digital preview and physical print.

**Prevention:** WeasyPrint supports embedding sRGB ICC profiles via the `srgb` parameter in its API. Enable it for the print PDF variant. Use `sRGB IEC61966-2.1` (the standard web sRGB profile).

**Phase:** Print PDF output (Phase 3).

---

### Pitfall 16: Three-Edition File Naming Confusion at Upload Time

**What goes wrong:** With English-only, Korean-only, and Bilingual editions each producing a screen PDF and a print PDF, the publish package contains 6 files (plus covers). Uploading the wrong file to the wrong KDP/Gumroad product is easy under time pressure.

**Prevention:**
- Enforce a strict naming convention: `{slug}_{edition}_{variant}.pdf` (e.g., `dangun_bilingual_print.pdf`, `dangun_english_screen.pdf`).
- The publish package should include a `CHECKLIST.txt` explicitly listing which file goes where.

**Phase:** Publish command (Phase 4).

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|---|---|---|
| Style guide YAML design | Character description drift if prompts use loose natural language | Lock exact token strings for each character in the style guide; treat them as code constants, not prose |
| Image generation pipeline | Cold start hangs + no resume on crash | State file before first API call; async polling with progress output |
| Flux reference image setup | Multi-character confusion | Stitch reference images into single combined input |
| Bilingual layout CSS | Korean text silently blank | `@font-face url()` with bundled Noto KR; preflight render check |
| Bilingual layout design | Language hierarchy signal | Match font size and weight for both languages; get Korean-speaker sign-off on template |
| Print PDF generation | Bleed clips at page boundary | Use sized elements with negative margins, not CSS page backgrounds |
| Print PDF generation | Crop marks cause KDP rejection | `marks: none` in KDP variant; `marks: crop` only in proofing variant |
| Print PDF generation | 300 DPI minimum not met | Validate pixel dimensions in `build`; upscale if needed |
| Cover generation | Spine width wrong after page count changes | Calculate spine from current page count at publish time, not design time |
| KDP submission | AI disclosure question skipped | Embed reminder in publish checklist output |
| KDP submission | Wrong edition PDF uploaded | Strict naming convention + CHECKLIST.txt in publish package |
| Style regeneration months later | Model weights updated, style drifts | Pin Replicate model version hash in style guide config |

---

## Sources

- Black Forest Labs, FLUX.1 Kontext official docs: https://docs.bfl.ml/guides/prompting_guide_kontext_i2i
- Together AI blog on Flux Kontext character consistency: https://www.together.ai/blog/flux-1-kontext
- WeasyPrint GitHub issue #934 (bleed clipping): https://github.com/Kozea/WeasyPrint/issues/934
- WeasyPrint GitHub issue #2120 (CJK font slowdown): https://github.com/Kozea/WeasyPrint/issues/2120
- WeasyPrint GitHub issue #2366 (Korean blank text): https://github.com/Kozea/WeasyPrint/issues/2366
- WeasyPrint color/ICC support blog: https://www.courtbouillon.org/blog/00052-more-colors-in-weasyprint/
- KDP Paperback Submission Guidelines (official): https://kdp.amazon.com/en_US/help/topic/G201857950
- KDP Set Trim Size, Bleed, and Margins (official): https://kdp.amazon.com/en_US/help/topic/GVBQ3CMEQW3W2VL6
- KDP Create a Paperback Cover (official): https://kdp.amazon.com/en_US/help/topic/G201953020
- KDP AI content disclosure rules 2025: https://www.brandonrohrbaugh.com/blog/kdp-ai-disclosure-rules-2025-explained
- KDP quality rejections checklist 2025: https://www.falconedits.com/kdp-quality-rejections-in-2025-the-editing-formatting-checklist-to-pass-review-first-time/
- KDP cover rejection checklist 2026: https://bookcoverslab.com/guides/kdp-cover-rejection-checklist-2026
- AI children's book character consistency pipeline: https://www.musketeerstech.com/for-ai/consistent-characters-ai-childrens-books/
- AI character generator consistency benchmark 2026: https://www.neolemon.com/blog/best-ai-character-generator-consistency-benchmark/
- Replicate prediction lifecycle (official): https://replicate.com/docs/topics/predictions/lifecycle
- Replicate cold start behavior (official): https://replicate.com/docs/how-does-replicate-work
- Bilingual typography implications for picture books: https://www.tandfonline.com/doi/full/10.1080/1051144X.2023.2168397
- KDP spine width calculator guide: https://www.kdpeasy.com/blog/spine-width-calculator-guide
