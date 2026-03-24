# Upload Checklist: {{ title }}

Generated: {{ date }}

## Gumroad Upload

1. Go to gumroad.com/products/new
2. Title: {{ gumroad.title }}
3. Price: ${{ gumroad.price }}
4. Description: (copy from LISTING-COPY.md, Gumroad section)
5. Upload files: all PDFs from this package
6. Upload thumbnail: gumroad-thumb.png
7. Set tags: children's book, bilingual, Korean, English

## KDP Upload

1. Go to kdp.amazon.com -> Create New Title
2. Title: {{ kdp.title }}
3. Subtitle: {{ kdp.subtitle }}
4. Description: (copy from LISTING-COPY.md, KDP section)
5. Keywords: {{ kdp.keywords | join(", ") }}
6. Upload manuscript PDF (print edition)
7. Upload cover: kdp-cover.png ({{ kdp_cover_w }}" x {{ kdp_cover_h }}")
8. Set trim size: {{ trim_size }}
9. Set price: ${{ kdp.price }}

## AI Content Disclosure

**IMPORTANT:** KDP requires disclosure of AI-generated content.

- In the "AI-generated content" section, select **YES** for AI-generated images
- Note: "Illustrations created with AI image generation (Flux Kontext Pro)"
- Text content: select YES if story was AI-drafted, NO if fully human-written
- This is a legal requirement -- do not skip this step
