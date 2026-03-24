"""Render a Book model into edition-aware HTML via Jinja2 templates.

This module produces HTML strings for WeasyPrint consumption. It does NOT
generate PDFs — that is handled by the PDF builder in plan 03-02.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from bookforge.story.schema import Book
from bookforge.style.schema import StyleGuide

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
TEMPLATES_DIR = ASSETS_DIR / "templates"
FONTS_DIR = ASSETS_DIR / "fonts"


def render_book_html(
    book: Book,
    edition: str,
    style_guide: StyleGuide,
    fmt: str,
    book_dir: Path,
) -> str:
    """Render a Book into an HTML string for a given edition and format.

    Args:
        book: The parsed Book model with pages and metadata.
        edition: Language edition — "en", "ko", or "bilingual".
        style_guide: StyleGuide with layout dimensions.
        fmt: Output format — "screen" or "print".
        book_dir: Book project directory (for resolving image paths).

    Returns:
        Rendered HTML string ready for WeasyPrint or browser preview.
    """
    # Parse trim size from book metadata (e.g. "8.5x8.5" -> 8.5, 8.5)
    trim_w, trim_h = _parse_trim_size(book.meta.trim_size)

    # Get layout parameters from style guide
    bleed = style_guide.layout.bleed_inches
    safe_margin = style_guide.layout.safe_margin_inches

    # Compute page dimensions based on format
    if fmt == "print":
        page_w = trim_w + 2 * bleed
        page_h = trim_h + 2 * bleed
    else:
        page_w = trim_w
        page_h = trim_h
        bleed = 0.0

    # Resolve paths
    font_path = (FONTS_DIR / "NotoSansKR-Regular.otf").resolve().as_uri()
    image_dir = (book_dir / "images").resolve()

    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("book_base.html.j2")

    # Render
    html = template.render(
        title=book.meta.title,
        pages=book.pages,
        edition=edition,
        fmt=fmt,
        image_dir=str(image_dir),
        font_path=font_path,
        trim_w=trim_w,
        trim_h=trim_h,
        page_w=page_w,
        page_h=page_h,
        bleed=bleed,
        safe_margin=safe_margin,
        base_url=str(book_dir.resolve()),
    )

    return html


def _parse_trim_size(trim_size: str) -> tuple[float, float]:
    """Parse a trim size string like '8.5x8.5' into (width, height) floats."""
    parts = trim_size.lower().split("x")
    if len(parts) != 2:
        raise ValueError(f"Invalid trim_size format: {trim_size!r} (expected 'WxH')")
    return float(parts[0]), float(parts[1])
