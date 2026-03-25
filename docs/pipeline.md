# BookForge Pipeline — How a Book Gets Made

## The People

- **Jeff** — writes stories (with Claude), runs the pipeline, handles tech
- **Wife** — proofreads Korean, reviews art, gives final approval
- **Claude** — writes stories, generates prompts, builds PDFs, manages pipeline
- **Flux Kontext** — generates illustrations from prompts (~$0.05/image)

## The Flow

```
 ┌─────────────────────────────────────────────────────────┐
 │  1. STORY                                               │
 │                                                         │
 │  Jeff + Claude write the story together                 │
 │  Claude writes bilingual English + Korean               │
 │  Output: books/<slug>/story.md                          │
 │                                                         │
 │  ┌──────────────────────────────────────┐               │
 │  │  uv run bookforge new <slug>         │  (scaffolds)  │
 │  └──────────────────────────────────────┘               │
 └──────────────────────┬──────────────────────────────────┘
                        │
                        ▼
 ┌─────────────────────────────────────────────────────────┐
 │  2. WIFE REVIEWS KOREAN TEXT                            │
 │                                                         │
 │  Push story.md + images to Google Drive (gws CLI)       │
 │  Wife reads on Chromebook, messages fixes via KakaoTalk │
 │  Jeff tells Claude the fixes, Claude updates story.md   │
 │  Repeat until wife approves Korean text                 │
 │                                                         │
 │  ┌──────────────────────────────────────┐               │
 │  │  gws drive files create --upload ... │  (sync)       │
 │  └──────────────────────────────────────┘               │
 └──────────────────────┬──────────────────────────────────┘
                        │
                        ▼
 ┌─────────────────────────────────────────────────────────┐
 │  3. CHARACTER REFERENCES (one-time per series)          │
 │                                                         │
 │  Generate 5-6 versions of each character                │
 │  Jeff picks the best ones                               │
 │  Save to style-guides/characters/                       │
 │  These get fed to EVERY future image generation         │
 │                                                         │
 │  Characters for Dangun:                                 │
 │  - Ho-rang (tiger) — appears in most books              │
 │  - Gom-i (bear) — appears in most books                 │
 │  - Hwanung (prince) — this book only                    │
 │  - Gom-i as human — this book only                      │
 │                                                         │
 │  Cost: ~$0.30 one-time for Ho-rang + Gom-i              │
 │  Book-specific characters: ~$0.15 per book              │
 └──────────────────────┬──────────────────────────────────┘
                        │
                        ▼
 ┌─────────────────────────────────────────────────────────┐
 │  4. ILLUSTRATE                                          │
 │                                                         │
 │  Generate one image per page using:                     │
 │  - Style guide prompt prefix (Korean Cute Watercolor)   │
 │  - Character reference images (consistency!)            │
 │  - Scene description from story.md                      │
 │                                                         │
 │  ┌──────────────────────────────────────┐               │
 │  │  uv run bookforge illustrate <slug>  │  (~$0.55)     │
 │  └──────────────────────────────────────┘               │
 │                                                         │
 │  Review contact sheet (all images on one page)          │
 │  Redo any bad ones: --redo 3,7                          │
 └──────────────────────┬──────────────────────────────────┘
                        │
                        ▼
 ┌─────────────────────────────────────────────────────────┐
 │  5. WIFE REVIEWS ART                                    │
 │                                                         │
 │  Push images to Google Drive (gws CLI)                  │
 │  Wife browses on Chromebook                             │
 │  Messages feedback via KakaoTalk                        │
 │  Jeff tells Claude → redo specific pages                │
 │  Repeat until wife approves art                         │
 └──────────────────────┬──────────────────────────────────┘
                        │
                        ▼
 ┌─────────────────────────────────────────────────────────┐
 │  6. BUILD PDFs                                          │
 │                                                         │
 │  6 PDFs from one story.md:                              │
 │                                                         │
 │  ┌────────────┬─────────┬─────────┬──────────┐         │
 │  │            │ English │ Korean  │ Bilingual │         │
 │  ├────────────┼─────────┼─────────┼──────────┤         │
 │  │ Screen     │   ✓     │   ✓     │    ✓     │ Gumroad │
 │  │ Print      │   ✓     │   ✓     │    ✓     │ KDP     │
 │  └────────────┴─────────┴─────────┴──────────┘         │
 │                                                         │
 │  ┌──────────────────────────────────────┐               │
 │  │  uv run bookforge build <slug>       │               │
 │  │                      --lang all      │               │
 │  └──────────────────────────────────────┘               │
 └──────────────────────┬──────────────────────────────────┘
                        │
                        ▼
 ┌─────────────────────────────────────────────────────────┐
 │  7. REVIEW                                              │
 │                                                         │
 │  Shows: page count, image count, word count, file sizes │
 │  Checklist: story quality, Korean proofed, art          │
 │  consistent, cover strong                               │
 │  Requires explicit yes/no approval                      │
 │                                                         │
 │  ┌──────────────────────────────────────┐               │
 │  │  uv run bookforge review <slug>      │               │
 │  └──────────────────────────────────────┘               │
 └──────────────────────┬──────────────────────────────────┘
                        │
                        ▼
 ┌─────────────────────────────────────────────────────────┐
 │  8. PUBLISH PACKAGE                                     │
 │                                                         │
 │  Generates publish-package/ with:                       │
 │  - All 6 PDFs                                           │
 │  - Cover images (Gumroad thumb, KDP cover, social)      │
 │  - Listing copy (title, description, price)             │
 │  - Upload checklist (incl. AI disclosure reminder)      │
 │                                                         │
 │  ┌──────────────────────────────────────┐               │
 │  │  uv run bookforge publish <slug>     │               │
 │  └──────────────────────────────────────┘               │
 └──────────────────────┬──────────────────────────────────┘
                        │
                        ▼
 ┌─────────────────────────────────────────────────────────┐
 │  9. MANUAL UPLOAD                                       │
 │                                                         │
 │  Gumroad: upload screen PDFs + cover + listing copy     │
 │  KDP: upload print PDFs + KDP cover + listing copy      │
 │  Follow the generated UPLOAD-CHECKLIST.md               │
 │  (includes AI content disclosure reminder)              │
 └─────────────────────────────────────────────────────────┘


## Content Calendar

 ┌─────────────────────────────────────────────────────────┐
 │  uv run bookforge calendar                              │
 │                                                         │
 │  Shows upcoming releases with backward-planned dates:   │
 │                                                         │
 │  Book         │ Holiday        │ Release   │ Story Due  │
 │  ─────────────┼────────────────┼───────────┼──────────  │
 │  dangun       │ Heritage Month │ Apr 11    │ Mar 15     │
 │  admiral-yi   │ 광복절         │ Jul 25    │ Jun 28     │
 │  heungbu      │ 추석           │ Sep 5     │ Aug 8      │
 │  christmas-kr │ Christmas      │ Dec 5     │ Nov 8      │
 └─────────────────────────────────────────────────────────┘


## Cost Per Book

 ┌─────────────────────────────────────────────────────────┐
 │                                                         │
 │  Character refs (reusable):  $0.30 (one-time)           │
 │  Book-specific characters:   $0.15                      │
 │  Page illustrations (12):    $0.55                      │
 │  Redos (estimate 5):         $0.25                      │
 │  ────────────────────────────────────                   │
 │  Total per book:             ~$1-2                      │
 │                                                         │
 │  One Gumroad sale ($4.99) pays for 3-5 books            │
 │                                                         │
 └─────────────────────────────────────────────────────────┘


## Collaboration Flow (Jeff ↔ Wife)

 ┌──────────┐     story.md      ┌──────────────┐
 │          │ ──── gws ────────→│              │
 │   Jeff   │     images/       │ Google Drive │
 │ (Claude) │ ──── gws ────────→│              │
 │          │                   └──────┬───────┘
 │          │                          │
 │          │                          ▼
 │          │                   ┌──────────────┐
 │          │                   │  Wife reads   │
 │          │                   │  on Chromebook│
 │          │                   └──────┬───────┘
 │          │                          │
 │          │      KakaoTalk           │
 │          │ ◄──── feedback ──────────┘
 │          │  "page 8 한국어 고쳐줘"
 │          │  "tiger looks weird p14"
 │          │
 │  Claude  │
 │  fixes   │
 │  & re-   │
 │  generates│
 │          │ ──── gws ────────→ (updated files)
 └──────────┘
