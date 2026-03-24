"""CLI illustrate command for generating book page illustrations."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer

from bookforge.images.contact_sheet import generate_contact_sheet
from bookforge.images.service import generate_all
from bookforge.state import load_state
from bookforge.story.parser import parse_story
from bookforge.style.loader import load_style_guide


def illustrate_command(
    slug: str = typer.Argument(..., help="Book slug (directory name under books/)"),
    redo: str | None = typer.Option(
        None, "--redo", help="Comma-separated page numbers to regenerate"
    ),
) -> None:
    """Generate illustrations for all pages in a book."""
    book_dir = Path("books") / slug
    if not book_dir.exists():
        typer.echo(f"Error: Book directory not found: {book_dir}", err=True)
        raise typer.Exit(1)

    # Load book and style guide
    book = parse_story(book_dir / "story.md")
    style_guide_path = (
        book_dir.parent / "style-guides" / f"{book.meta.style_guide}.yaml"
    )
    style_guide = load_style_guide(style_guide_path)

    # Parse redo pages
    redo_pages: list[int] | None = None
    if redo:
        redo_pages = [int(p.strip()) for p in redo.split(",")]

    # Run generation
    state = asyncio.run(
        generate_all(book_dir, book, style_guide, redo_pages=redo_pages)
    )

    # Collect image paths from state
    image_paths: list[Path] = []
    pages_ok = 0
    pages_failed = 0
    pages_skipped = 0
    for page in book.pages:
        page_key = str(page.number)
        page_state = state.get("pages", {}).get(page_key, {})
        if page_state.get("status") == "ok" and page_state.get("image_path"):
            image_paths.append(book_dir / page_state["image_path"])
            pages_ok += 1
        elif page_state.get("status") == "failed":
            pages_failed += 1
        else:
            pages_skipped += 1

    # Generate contact sheet
    cs_path = generate_contact_sheet(book_dir, image_paths)

    # Print summary
    typer.echo(f"Illustration complete for '{slug}'")
    typer.echo(f"  Pages generated: {pages_ok}")
    if pages_skipped:
        typer.echo(f"  Pages skipped: {pages_skipped}")
    if pages_failed:
        typer.echo(f"  Pages failed: {pages_failed}")
    typer.echo(f"  Contact sheet: {cs_path}")
