"""BookForge CLI entry point."""

import typer

from bookforge.cli.build import build_command
from bookforge.cli.calendar import calendar_command
from bookforge.cli.illustrate import illustrate_command
from bookforge.cli.new import new_command
from bookforge.cli.review import review_command

app = typer.Typer(
    name="bookforge",
    help="Bilingual children's book production pipeline.",
    no_args_is_help=True,
)

app.command("new")(new_command)
app.command("illustrate")(illustrate_command)
app.command("build")(build_command)
app.command("review")(review_command)
app.command("calendar")(calendar_command)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Bilingual children's book production pipeline."""
    if ctx.invoked_subcommand is None:
        pass
