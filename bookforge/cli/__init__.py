"""BookForge CLI entry point."""

import typer

app = typer.Typer(
    name="bookforge",
    help="Bilingual children's book production pipeline.",
    no_args_is_help=True,
)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Bilingual children's book production pipeline."""
    if ctx.invoked_subcommand is None:
        pass
