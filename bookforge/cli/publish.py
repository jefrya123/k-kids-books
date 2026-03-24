"""CLI publish command for generating upload-ready packages."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from bookforge.publish.package import create_publish_package
from bookforge.state import load_state
from bookforge.story.parser import parse_story

console = Console()


def publish_command(
    slug: str = typer.Argument(..., help="Book slug (directory name under books/)"),
    books_dir: Path = typer.Option(
        "books", "--books-dir", help="Parent directory containing book folders"
    ),
) -> None:
    """Generate a complete publish package for upload to Gumroad and KDP."""
    book_dir = books_dir / slug
    if not book_dir.exists():
        typer.echo(f"Error: Book directory not found: {book_dir}", err=True)
        raise typer.Exit(1)

    # Check review approval before doing any work
    state = load_state(book_dir)
    if not state.get("review_approved"):
        console.print(
            "[bold red]Book not approved for publishing.[/bold red]\n"
            f"Run `bookforge review {slug}` first."
        )
        raise typer.Exit(1)

    # Load book
    book = parse_story(book_dir / "story.md")

    # Create package
    console.print(f"\n[bold]Creating publish package for:[/bold] {book.meta.title}")
    try:
        pkg_dir = create_publish_package(book, book_dir)
    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1) from e

    # Print summary
    console.print(f"\n[bold green]Publish package created![/bold green]")
    console.print(f"\n[bold]Package contents:[/bold]")

    total_size = 0
    for f in sorted(pkg_dir.iterdir()):
        size = f.stat().st_size
        total_size += size
        if size > 1024 * 1024:
            size_str = f"{size / 1024 / 1024:.1f} MB"
        elif size > 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size} B"
        console.print(f"  {f.name:40s} {size_str}")

    zip_path = book_dir / "publish-package.zip"
    if zip_path.exists():
        zip_size = zip_path.stat().st_size
        if zip_size > 1024 * 1024:
            zip_str = f"{zip_size / 1024 / 1024:.1f} MB"
        else:
            zip_str = f"{zip_size / 1024:.1f} KB"
        console.print(f"\n[bold]Zip archive:[/bold] {zip_path.name} ({zip_str})")

    console.print(
        f"\n[dim]Review UPLOAD-CHECKLIST.md for step-by-step upload instructions.[/dim]"
    )
