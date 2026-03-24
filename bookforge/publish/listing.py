"""Listing copy generation for Gumroad and KDP.

Auto-generates platform-specific listing text from book metadata,
including AI content disclosure in descriptions.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from bookforge.story.schema import Book

# Path to Jinja2 templates
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "assets" / "templates"


def generate_listing_copy(book: Book, page_count: int) -> dict:
    """Generate listing copy for Gumroad and KDP.

    Returns dict with 'gumroad' and 'kdp' keys, each containing
    platform-specific listing data.
    """
    meta = book.meta
    bilingual_title = f"{meta.title} / {meta.title_ko}"

    gumroad_desc = (
        f"{bilingual_title}\n\n"
        f"A beautifully illustrated bilingual English/Korean children's book "
        f"for ages {meta.ages}.\n\n"
        f"{page_count} pages of engaging story with full-color illustrations.\n\n"
        f"Includes PDF formats for screen reading and printing.\n\n"
        f"Illustrated with AI assistance (Flux Kontext Pro)."
    )

    kdp_desc = (
        f"{bilingual_title}\n\n"
        f"A beautifully illustrated bilingual English/Korean children's book "
        f"designed for ages {meta.ages}. This {page_count}-page picture book "
        f"features vivid, full-color illustrations on every page.\n\n"
        f"Perfect for bilingual families, Korean language learners, and anyone "
        f"who loves charming children's stories. Each page presents the story "
        f"in both English and Korean, making it an excellent educational resource.\n\n"
        f"Illustrated with AI assistance."
    )

    # Generate 7 keywords from title and standard terms
    title_words = [w for w in meta.title.split() if len(w) > 2]
    base_keywords = [
        "Korean children's book",
        "bilingual",
        "English Korean",
        "picture book",
        f"ages {meta.ages}",
    ]
    # Fill remaining slots with title words
    keywords = base_keywords[:]
    for word in title_words:
        if len(keywords) >= 7:
            break
        if word.lower() not in [k.lower() for k in keywords]:
            keywords.append(word)
    # Pad if needed
    while len(keywords) < 7:
        keywords.append("children's story")
    keywords = keywords[:7]

    return {
        "gumroad": {
            "title": bilingual_title,
            "description": gumroad_desc,
            "price": meta.price,
        },
        "kdp": {
            "title": meta.title,
            "subtitle": meta.title_ko,
            "description": kdp_desc,
            "price": meta.price,
            "keywords": keywords,
        },
    }


def render_upload_checklist(
    book: Book,
    listing: dict,
    kdp_cover_dims: tuple[float, float],
) -> str:
    """Render the upload checklist template with book-specific data.

    Args:
        book: The parsed Book model.
        listing: Output from generate_listing_copy().
        kdp_cover_dims: (width_inches, height_inches) of KDP cover.

    Returns:
        Rendered markdown string.
    """
    from datetime import datetime

    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        keep_trailing_newline=True,
    )
    template = env.get_template("UPLOAD-CHECKLIST.md")

    return template.render(
        title=book.meta.title,
        date=datetime.now().strftime("%Y-%m-%d"),
        gumroad=listing["gumroad"],
        kdp=listing["kdp"],
        kdp_cover_w=f"{kdp_cover_dims[0]:.2f}",
        kdp_cover_h=f"{kdp_cover_dims[1]:.2f}",
        trim_size=book.meta.trim_size,
    )
