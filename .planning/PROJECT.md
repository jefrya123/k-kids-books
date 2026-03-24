# BookForge — Bilingual Korean Children's Book Pipeline

## What This Is

A Python CLI tool that produces bilingual Korean/English children's books with consistent AI-generated art. Takes a markdown story file through a pipeline of story generation, illustration, layout, and publishing — with human review gates at every stage. Built by a Korean-American couple selling on Gumroad (digital) and Amazon KDP (print-on-demand).

## Core Value

Consistent, high-quality children's book illustrations from a single markdown file — the pipeline must produce books that look hand-illustrated, not AI-generated, with characters that are recognizably the same across all pages.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] CLI tool with `new`, `illustrate`, `build`, `review`, `publish`, `calendar` commands
- [ ] Style guide system (YAML) defining art style, characters, color palette, prompt prefixes
- [ ] Story generation from Claude API with bilingual English/Korean output
- [ ] Image generation via provider-agnostic interface (Flux Kontext default) with character reference images
- [ ] Three language editions per book: English-only, Korean-only, Bilingual
- [ ] Screen PDF output (RGB, no bleed) for Gumroad
- [ ] Print PDF output (RGB + sRGB ICC, bleed, trim marks, 300 DPI) for KDP
- [ ] Human review gates at story, illustration, final review, and publish steps
- [ ] Content calendar with holiday-driven release scheduling (release 2-3 weeks before holidays)
- [ ] Publish package generation (files + listing copy for manual Gumroad/KDP upload)
- [ ] Two recurring mascot characters: Ho-rang (tiger) and Gom-i (bear)
- [ ] Image retry/resume (skip completed, retry failures, `--redo` for specific pages)
- [ ] Story markdown format with YAML frontmatter, page boundaries, bilingual text blocks, image prompts

### Out of Scope

- Web dashboard / GUI editor — CLI is sufficient for 1 book/month
- Automated Gumroad/KDP upload — no public APIs, manual upload with generated package
- ePub format — PDF only for v1
- Audio pronunciation — future feature
- Social media automation — future feature
- IngramSpark distribution — add when demand proven
- Traditional publishing outreach — build catalog first

## Context

- Series: "Ho-rang & Gom-i's Korean Adventures" — tiger and bear mascots guide kids through Korean history and folk tales
- Art style: "Korean Cute Watercolor" — simple rounded characters (Kakao-ish) with soft watercolor backgrounds
- Target: ages 4-8, ~20 pages per book, $3.99-4.99 digital / KDP print pricing
- Cadence: 1 book/month to start, scale if demand
- Image budget: ~$10-15/book (~$0.04-1.00/image depending on provider)
- POC exists: Dangun story fully written with HTML preview at `poc/dangun-book.md`
- Wife proofreads Korean text — human gate before illustration
- Holiday calendar: Asian American Heritage Month (May), 광복절 (Aug), 추석 (Sep), Christmas (Dec)

## Constraints

- **Image consistency**: Characters must look the same across all pages — this is the hardest technical challenge
- **Budget**: Image generation should stay under $15/book
- **Dependencies**: Requires Replicate API token (Flux) and Anthropic API key (Claude)
- **Print specs**: KDP has specific trim size, bleed, and cover dimension requirements
- **Timeline**: MVP wanted ASAP — wife is in Korea, want to show her progress today

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Flux Kontext over DALL-E 3 | IP-Adapter/Kontext supports character reference images; DALL-E 3 does not | — Pending |
| Provider-agnostic image layer | Swap providers via config, not code changes | — Pending |
| RGB not CMYK for print | WeasyPrint can't do CMYK; KDP converts internally from sRGB | — Pending |
| Manual upload over API | Gumroad/KDP have no public product-creation APIs | — Pending |
| Square 8.5x8.5" trim | Most common KDP children's picture book format | — Pending |
| Ho-rang & Gom-i mascots | Recurring characters build brand + easier AI consistency | — Pending |

---
*Last updated: 2026-03-24 after initialization*
