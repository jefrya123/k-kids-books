"""CLI build command for generating PDF books."""

from __future__ import annotations

from pathlib import Path

import typer

from bookforge.build.pdf import build_pdf
from bookforge.build.renderer import render_book_html
from bookforge.story.parser import parse_story
from bookforge.style.loader import load_style_guide

ALL_EDITIONS = ["en", "ko", "bilingual"]
ALL_FORMATS = ["screen", "print"]


def build_command(
    slug: str = typer.Argument(..., help="Book slug (directory name under books/)"),
    lang: str = typer.Option(
        "bilingual", "--lang", "-l", help="Edition: en, ko, bilingual, all"
    ),
    fmt: str = typer.Option(
        "all", "--format", "-f", help="Format: screen, print, all"
    ),
) -> None:
    """Build PDF files for a book."""
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

    # Determine editions and formats
    editions = ALL_EDITIONS if lang == "all" else [lang]
    formats = ALL_FORMATS if fmt == "all" else [fmt]

    # Parse trim size from book metadata
    parts = book.meta.trim_size.lower().split("x")
    trim_inches = (float(parts[0]), float(parts[1]))
    bleed_inches = style_guide.layout.bleed_inches

    # Create output directory
    output_dir = book_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    generated: list[tuple[str, str, Path]] = []

    for edition in editions:
        for format_name in formats:
            typer.echo(f"Building {edition} {format_name}...")
            html = render_book_html(book, edition, style_guide, format_name, book_dir)
            output_path = output_dir / f"{slug}-{edition}-{format_name}.pdf"
            build_pdf(
                html_string=html,
                output_path=output_path,
                fmt=format_name,
                trim_inches=trim_inches,
                bleed_inches=bleed_inches,
                book_dir=book_dir,
            )
            generated.append((edition, format_name, output_path))

    # Print summary
    typer.echo("")
    typer.echo(f"Build complete for '{slug}': {len(generated)} PDF(s)")
    for edition, format_name, path in generated:
        size_kb = path.stat().st_size / 1024
        typer.echo(f"  {path.name}  ({edition}, {format_name})  {size_kb:.1f} KB")
