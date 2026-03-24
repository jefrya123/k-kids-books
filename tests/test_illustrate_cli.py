"""Tests for the illustrate CLI command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from bookforge.cli import app


runner = CliRunner()


@pytest.fixture
def mock_book_dir(tmp_path: Path, monkeypatch):
    """Set up a fake books/ directory with required files."""
    books_dir = tmp_path / "books"
    book_dir = books_dir / "test-book"
    (book_dir / "images").mkdir(parents=True)

    # Create a minimal story.md
    story_md = """\
---
title: "Test Book"
title_ko: "테스트 책"
slug: test-book
trim_size: "8.5x8.5"
price: 4.99
ages: "4-8"
style_guide: korean-cute-watercolor
---

## Page 1

Hello world.

<!-- ko -->
안녕하세요.
<!-- /ko -->

<!-- image: A happy scene -->
"""
    (book_dir / "story.md").write_text(story_md)

    # Create style guide
    style_dir = books_dir / "style-guides"
    style_dir.mkdir(parents=True)
    from ruamel.yaml import YAML

    yaml = YAML()
    style_data = {
        "name": "korean-cute-watercolor",
        "version": 1,
        "art_style": {
            "prompt_prefix": "Cute style",
            "negative_prompt": "dark",
            "color_palette": ["#FFF"],
        },
        "image": {"provider": "flux_kontext_pro", "width": 1024, "height": 1024},
        "characters": {
            "char1": {
                "name_en": "Char",
                "name_ko": "캐릭",
                "description": "A character",
                "reference_image": "characters/char.png",
            }
        },
    }
    with open(style_dir / "korean-cute-watercolor.yaml", "w") as f:
        yaml.dump(style_data, f)

    # Monkeypatch cwd to tmp_path so "books/test-book" resolves
    monkeypatch.chdir(tmp_path)
    return book_dir


class TestIllustrateCli:
    def test_illustrate_cli_invokes_service(self, mock_book_dir):
        """CLI command loads book + style guide, calls generate_all, then contact sheet."""
        mock_state = {
            "pages": {
                "1": {
                    "status": "ok",
                    "image_path": "images/page-01-v1.png",
                    "image_version": 1,
                }
            }
        }

        with (
            patch(
                "bookforge.cli.illustrate.generate_all",
                new_callable=AsyncMock,
                return_value=mock_state,
            ) as mock_gen,
            patch(
                "bookforge.cli.illustrate.generate_contact_sheet",
                return_value=mock_book_dir / "images" / "contact-sheet.html",
            ) as mock_cs,
        ):
            result = runner.invoke(app, ["illustrate", "test-book"])

        assert result.exit_code == 0, result.output
        mock_gen.assert_called_once()
        mock_cs.assert_called_once()

    def test_illustrate_cli_redo_flag(self, mock_book_dir):
        """--redo '3,7' parses to redo_pages=[3, 7] passed to generate_all."""
        mock_state = {"pages": {}}

        with (
            patch(
                "bookforge.cli.illustrate.generate_all",
                new_callable=AsyncMock,
                return_value=mock_state,
            ) as mock_gen,
            patch(
                "bookforge.cli.illustrate.generate_contact_sheet",
                return_value=mock_book_dir / "images" / "contact-sheet.html",
            ),
        ):
            result = runner.invoke(app, ["illustrate", "test-book", "--redo", "3,7"])

        assert result.exit_code == 0, result.output
        call_kwargs = mock_gen.call_args
        assert call_kwargs.kwargs.get("redo_pages") == [3, 7] or (
            len(call_kwargs.args) >= 4 and call_kwargs.args[3] == [3, 7]
        )

    def test_illustrate_cli_registered(self):
        """'illustrate' appears in CLI help."""
        result = runner.invoke(app, ["--help"])
        assert "illustrate" in result.output
