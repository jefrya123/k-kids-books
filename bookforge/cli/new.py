"""bookforge new <slug> -- scaffold a new book directory with story template."""

from pathlib import Path

import typer
from rich.console import Console

from bookforge.state import save_state

console = Console()

STORY_TEMPLATE = """---
title: "{title}"
title_ko: ""
subtitle: ""
slug: {slug}
trim_size: "8.5x8.5"
price: 4.99
ages: "4-8"
---

## Page 1 — Title Page

<!-- image: Ho-rang and Gom-i standing together in front of a beautiful scene. Warm golden light. Cute Korean watercolor style. -->

## Page 2-3

<!-- ko -->
<!-- /ko -->

<!-- image: -->

## Page 4-5

<!-- ko -->
<!-- /ko -->

<!-- image: -->

## Page 6-7

<!-- ko -->
<!-- /ko -->

<!-- image: -->

## Page 8-9

<!-- ko -->
<!-- /ko -->

<!-- image: -->

## Page 10-11

<!-- ko -->
<!-- /ko -->

<!-- image: -->

## Page 12-13

<!-- ko -->
<!-- /ko -->

<!-- image: -->

## Page 14-15

<!-- ko -->
<!-- /ko -->

<!-- image: -->

## Page 16-17

<!-- ko -->
<!-- /ko -->

<!-- image: -->

## Page 18-19

<!-- ko -->
<!-- /ko -->

<!-- image: -->

## Page 20 — Back Page

<!-- image: Ho-rang and Gom-i waving goodbye. Soft watercolor background. -->
"""


def new_command(
    slug: str = typer.Argument(..., help="Book slug, e.g. 'dangun-story'"),
    title: str = typer.Option("", "--title", "-t", help="Book title (optional, can edit later)"),
    style_guide: str = typer.Option("korean-cute-watercolor", "--style", "-s", help="Style guide name"),
) -> None:
    """Create a new book directory with a story.md template to fill in."""
    book_dir = Path("books") / slug

    if book_dir.exists():
        console.print(f"[red]Error:[/red] {book_dir} already exists.", style="bold")
        raise typer.Exit(1)

    # Create directory tree
    for subdir in ["images", "dist", "publish"]:
        (book_dir / subdir).mkdir(parents=True)

    # Write story template
    story_content = STORY_TEMPLATE.format(title=title or slug.replace("-", " ").title(), slug=slug)
    (book_dir / "story.md").write_text(story_content)

    # Write initial state
    save_state(book_dir, {
        "version": 1,
        "slug": slug,
        "style_guide": style_guide,
        "stages": {
            "story": "pending",
            "illustrate": "pending",
            "build_en": "pending",
            "build_ko": "pending",
            "build_bilingual": "pending",
            "publish": "pending",
        },
        "pages": {},
    })

    console.print(f"\n[green]Book scaffolded:[/green] {book_dir}/")
    console.print("  story.md      - Template ready to fill in")
    console.print("  state.json    - Pipeline state tracker")
    console.print("  images/       - Generated illustrations (empty)")
    console.print("  dist/         - Built PDFs (empty)")
    console.print("  publish/      - Final publish-ready files (empty)")
    console.print(f"\n[bold]Next steps:[/bold]")
    console.print(f"  1. Write your story in books/{slug}/story.md")
    console.print(f"     (or ask Claude to write it for you!)")
    console.print(f"  2. Have your wife proofread the Korean")
    console.print(f"  3. Run: uv run bookforge illustrate {slug}")
