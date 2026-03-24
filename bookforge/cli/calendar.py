"""CLI calendar command -- display upcoming release deadlines."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from bookforge.calendar import compute_deadlines, get_upcoming, load_calendar

EXAMPLE_YAML = """\
- holiday_name: "Chuseok"
  holiday_date: 2026-09-25
  slug: chuseok-story
  status: planned
- holiday_name: "Christmas"
  holiday_date: 2026-12-25
  slug: christmas-story
  status: planned
"""


def calendar_command(
    show_all: bool = typer.Option(False, "--all", help="Show all entries including past"),
) -> None:
    """Display upcoming release deadlines from content-calendar.yaml."""
    console = Console(width=200)
    calendar_path = Path("content-calendar.yaml")

    try:
        entries = load_calendar(calendar_path)
    except FileNotFoundError:
        console.print(
            "[red]Error:[/red] content-calendar.yaml not found in current directory.\n"
        )
        console.print("Create one with this format:\n")
        console.print(f"[dim]{EXAMPLE_YAML}[/dim]")
        raise typer.Exit(code=1)

    if not show_all:
        entries = get_upcoming(entries)

    if not entries:
        console.print("[yellow]No upcoming entries in content-calendar.yaml.[/yellow]")
        raise typer.Exit()

    table = Table(title="Content Calendar")
    table.add_column("Holiday", style="bold", no_wrap=True)
    table.add_column("Date", no_wrap=True)
    table.add_column("Release", no_wrap=True)
    table.add_column("Mktg Start", no_wrap=True)
    table.add_column("Writing Start", no_wrap=True)
    table.add_column("Slug", style="dim", no_wrap=True)
    table.add_column("Status", no_wrap=True)

    for entry in entries:
        deadlines = compute_deadlines(entry)

        status_style = {
            "done": "green",
            "in-progress": "yellow",
        }.get(entry.status, "")

        table.add_row(
            entry.holiday_name,
            entry.holiday_date.strftime("%Y-%m-%d"),
            deadlines["release_date"].strftime("%Y-%m-%d"),
            deadlines["marketing_start"].strftime("%Y-%m-%d"),
            deadlines["writing_start"].strftime("%Y-%m-%d"),
            entry.slug,
            f"[{status_style}]{entry.status}[/{status_style}]" if status_style else entry.status,
        )

    console.print(table)
