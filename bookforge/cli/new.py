"""bookforge new <slug> -- scaffold a new book and generate story draft."""

from pathlib import Path

import typer
from rich.console import Console

from bookforge.state import save_state
from bookforge.story.generator import generate_story

console = Console()


def new_command(
    slug: str = typer.Argument(..., help="Book slug, e.g. 'dangun-story'"),
    prompt: str = typer.Option(..., "--prompt", "-p", help="One-line book idea for Claude"),
    style_guide: str = typer.Option("korean-cute-watercolor", "--style", "-s", help="Style guide name"),
    pages: int = typer.Option(12, "--pages", help="Number of pages to generate"),
) -> None:
    """Create a new book directory and generate a bilingual story draft."""
    book_dir = Path("books") / slug

    if book_dir.exists():
        console.print(f"[red]Error:[/red] {book_dir} already exists.", style="bold")
        raise typer.Exit(1)

    # Create directory tree
    for subdir in ["images", "dist", "publish"]:
        (book_dir / subdir).mkdir(parents=True)

    # Generate story via Claude
    console.print(f"[cyan]Generating story for:[/cyan] {prompt}")
    story_content = generate_story(prompt, style_guide_name=style_guide, page_count=pages)
    (book_dir / "story.md").write_text(story_content)

    # Write initial state
    save_state(book_dir, {
        "version": 1,
        "slug": slug,
        "style_guide": style_guide,
        "stages": {
            "story": "complete",
            "illustrate": "pending",
            "build_en": "pending",
            "build_ko": "pending",
            "build_bilingual": "pending",
            "publish": "pending",
        },
        "pages": {},
    })

    console.print(f"\n[green]Book scaffolded:[/green] {book_dir}/")
    console.print("  story.md      - Generated bilingual draft")
    console.print("  state.json    - Pipeline state tracker")
    console.print("  images/       - Generated illustrations (empty)")
    console.print("  dist/         - Built PDFs (empty)")
    console.print("  publish/      - Final publish-ready files (empty)")
    console.print(f"\n[bold]Next steps:[/bold]")
    console.print(f"  1. Review and edit books/{slug}/story.md")
    console.print(f"  2. Run: uv run bookforge illustrate {slug}")
