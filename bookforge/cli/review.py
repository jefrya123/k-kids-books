"""CLI review command for pre-publish book review and approval."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from bookforge.review import REVIEW_CHECKLIST, format_summary, gather_summary
from bookforge.state import load_state, save_state
from bookforge.story.parser import parse_story

console = Console()


def review_command(
    slug: str = typer.Argument(..., help="Book slug (directory name under books/)"),
) -> None:
    """Review a book before publishing: display summary, checklist, and prompt for approval."""
    book_dir = Path("books") / slug
    if not book_dir.exists():
        typer.echo(f"Error: Book directory not found: {book_dir}", err=True)
        raise typer.Exit(1)

    # Load book
    book = parse_story(book_dir / "story.md")

    # Gather summary stats
    summary = gather_summary(book, book_dir)

    # Check for existing approval
    state = load_state(book_dir)
    if state.get("review_approved") is True:
        console.print(
            f"\n[bold green]Already approved on {state.get('review_date', 'unknown date')}[/bold green]\n"
        )
        console.print(format_summary(summary))
        return

    # Print summary table
    console.print()
    console.print(format_summary(summary))

    # Print PDF files
    if summary["pdf_files"]:
        console.print("\n[bold]PDF Files:[/bold]")
        for pdf in summary["pdf_files"]:
            console.print(f"  {pdf['name']}  ({pdf['size_kb']:.1f} KB)")
    else:
        console.print("\n[yellow]No PDF files found in output/[/yellow]")

    # Print checklist
    console.print("\n[bold]Review Checklist:[/bold]")
    for i, item in enumerate(REVIEW_CHECKLIST, start=1):
        console.print(f"  {i}. {item}")
    console.print()

    # Prompt for approval
    approved = typer.confirm("Approve this book for publishing?", default=False)

    if approved:
        state["review_approved"] = True
        state["review_date"] = datetime.now().isoformat()
        state["review_summary"] = summary
        save_state(book_dir, state)
        console.print("[bold green]Book approved for publishing![/bold green]")
    else:
        console.print("Review not approved.")
