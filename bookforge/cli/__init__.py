"""BookForge CLI entry point."""

import typer

app = typer.Typer(
    name="bookforge",
    help="Bilingual children's book production pipeline.",
    no_args_is_help=True,
)
