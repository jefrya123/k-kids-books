"""Publish package orchestration.

Creates a complete publish-package/ directory with all artifacts needed
for manual upload to Gumroad and KDP.
"""

import shutil
from pathlib import Path

from bookforge.publish.covers import (
    compute_kdp_cover_dimensions,
    compute_spine_width,
    generate_gumroad_thumb,
    generate_kdp_cover,
    generate_social_square,
)
from bookforge.publish.listing import generate_listing_copy, render_upload_checklist
from bookforge.state import load_state
from bookforge.story.schema import Book


def _find_cover_image(book_dir: Path) -> Path:
    """Find the cover image: images/cover.png or first page-01 image as fallback."""
    cover = book_dir / "images" / "cover.png"
    if cover.exists():
        return cover
    # Fallback: first page image
    images_dir = book_dir / "images"
    if images_dir.exists():
        for candidate in sorted(images_dir.glob("page-01*")):
            return candidate
    msg = f"No cover image found in {images_dir}"
    raise FileNotFoundError(msg)


def _format_listing_markdown(listing: dict) -> str:
    """Format listing copy as a readable markdown document."""
    gumroad = listing["gumroad"]
    kdp = listing["kdp"]

    lines = [
        "# Listing Copy",
        "",
        "## Gumroad",
        "",
        f"**Title:** {gumroad['title']}",
        f"**Price:** ${gumroad['price']}",
        "",
        "**Description:**",
        "",
        gumroad["description"],
        "",
        "---",
        "",
        "## KDP (Amazon)",
        "",
        f"**Title:** {kdp['title']}",
        f"**Subtitle:** {kdp['subtitle']}",
        f"**Price:** ${kdp['price']}",
        f"**Keywords:** {', '.join(kdp['keywords'])}",
        "",
        "**Description:**",
        "",
        kdp["description"],
        "",
    ]
    return "\n".join(lines)


def create_publish_package(book: Book, book_dir: Path) -> Path:
    """Create a complete publish package with all upload artifacts.

    Checks review approval, copies PDFs, generates cover images,
    listing copy, upload checklist, and creates a zip archive.

    Args:
        book: Parsed Book model.
        book_dir: Path to the book directory.

    Returns:
        Path to the publish-package/ directory.

    Raises:
        RuntimeError: If the book is not approved for publishing.
        FileNotFoundError: If cover image or PDFs are missing.
    """
    # Gate: review must be approved
    state = load_state(book_dir)
    if not state.get("review_approved"):
        msg = "Book not approved for publishing. Run `bookforge review` first."
        raise RuntimeError(msg)

    page_count = state.get("review_summary", {}).get("page_count", len(book.pages))

    # Create publish-package/ (clean slate)
    pkg_dir = book_dir / "publish-package"
    if pkg_dir.exists():
        shutil.rmtree(pkg_dir)
    pkg_dir.mkdir()

    # Copy all PDFs from output/
    output_dir = book_dir / "output"
    if output_dir.exists():
        for pdf in output_dir.glob("*.pdf"):
            shutil.copy2(pdf, pkg_dir / pdf.name)

    # Generate cover images
    cover_path = _find_cover_image(book_dir)
    trim_parts = book.meta.trim_size.split("x")
    trim_w = float(trim_parts[0])
    trim_h = float(trim_parts[1])

    generate_gumroad_thumb(cover_path, pkg_dir / "gumroad-thumb.png")
    generate_social_square(cover_path, pkg_dir / "social-square.png")
    generate_kdp_cover(cover_path, trim_w, trim_h, page_count, pkg_dir / "kdp-cover.png")

    # Generate listing copy
    listing = generate_listing_copy(book, page_count)
    listing_md = _format_listing_markdown(listing)
    (pkg_dir / "LISTING-COPY.md").write_text(listing_md)

    # Render upload checklist
    spine = compute_spine_width(page_count)
    kdp_dims = compute_kdp_cover_dimensions(trim_w, trim_h, spine)
    checklist = render_upload_checklist(book, listing, kdp_cover_dims=kdp_dims)
    (pkg_dir / "UPLOAD-CHECKLIST.md").write_text(checklist)

    # Create zip archive
    shutil.make_archive(
        str(book_dir / "publish-package"),
        "zip",
        root_dir=str(book_dir),
        base_dir="publish-package",
    )

    return pkg_dir
