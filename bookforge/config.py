"""Configuration and environment variable loading."""

import os

import typer


def get_anthropic_key() -> str:
    """Read ANTHROPIC_API_KEY from environment. Exit with clear error if missing."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        typer.echo(
            "Error: ANTHROPIC_API_KEY environment variable is not set.\n"
            "Get your API key at https://console.anthropic.com/settings/keys\n"
            "Then: export ANTHROPIC_API_KEY='sk-ant-...'",
            err=True,
        )
        raise typer.Exit(1)
    return key


def get_model() -> str:
    """Read BOOKFORGE_MODEL from environment, defaulting to claude-sonnet-4-5."""
    return os.environ.get("BOOKFORGE_MODEL", "claude-sonnet-4-5")
