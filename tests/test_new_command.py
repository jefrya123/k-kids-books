"""Tests for the bookforge new CLI command."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from bookforge.cli import app

runner = CliRunner()

SAMPLE_STORY = """\
---
title: "Test Story"
title_ko: "테스트 이야기"
slug: test-book
trim_size: "8.5x8.5"
price: 4.99
ages: "4-8"
style_guide: korean-cute-watercolor
---

## Page 1

Once upon a time there was a test.

<!-- ko -->
옛날 옛적에 테스트가 있었어요.
<!-- /ko -->

<!-- image: A simple test illustration -->
"""


class TestNewCommand:
    """Tests for bookforge new subcommand."""

    @patch("bookforge.cli.new.generate_story", return_value=SAMPLE_STORY)
    def test_creates_book_directory(self, mock_gen, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """new command creates books/<slug>/ directory."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["new", "test-book", "--prompt", "A test story"])
        assert result.exit_code == 0
        assert (tmp_path / "books" / "test-book").is_dir()

    @patch("bookforge.cli.new.generate_story", return_value=SAMPLE_STORY)
    def test_creates_subdirectories(self, mock_gen, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """new command creates images/, dist/, publish/ subdirectories."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["new", "test-book", "--prompt", "A test story"])
        assert result.exit_code == 0
        book_dir = tmp_path / "books" / "test-book"
        assert (book_dir / "images").is_dir()
        assert (book_dir / "dist").is_dir()
        assert (book_dir / "publish").is_dir()

    @patch("bookforge.cli.new.generate_story", return_value=SAMPLE_STORY)
    def test_writes_story_md(self, mock_gen, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """new command writes story.md with generated content."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["new", "test-book", "--prompt", "A test story"])
        assert result.exit_code == 0
        story_file = tmp_path / "books" / "test-book" / "story.md"
        assert story_file.exists()
        content = story_file.read_text()
        assert "## Page 1" in content

    @patch("bookforge.cli.new.generate_story", return_value=SAMPLE_STORY)
    def test_writes_state_json(self, mock_gen, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """new command writes state.json with correct initial state."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["new", "test-book", "--prompt", "A test story"])
        assert result.exit_code == 0
        state_file = tmp_path / "books" / "test-book" / "state.json"
        assert state_file.exists()
        state = json.loads(state_file.read_text())
        assert state["slug"] == "test-book"
        assert state["style_guide"] == "korean-cute-watercolor"
        assert state["stages"]["story"] == "complete"
        assert state["stages"]["illustrate"] == "pending"

    @patch("bookforge.cli.new.generate_story", return_value=SAMPLE_STORY)
    def test_error_on_existing_slug(self, mock_gen, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """new command exits with error if book directory already exists."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "books" / "test-book").mkdir(parents=True)
        result = runner.invoke(app, ["new", "test-book", "--prompt", "A test story"])
        assert result.exit_code == 1
        assert "already exists" in result.output or "already exists" in (result.stderr or "")

    def test_new_subcommand_registered(self) -> None:
        """bookforge --help shows 'new' subcommand."""
        result = runner.invoke(app, ["--help"])
        assert "new" in result.output

    @patch("bookforge.cli.new.generate_story", return_value=SAMPLE_STORY)
    def test_custom_style_guide(self, mock_gen, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """--style option is passed through to generate_story and saved in state."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["new", "test-book", "--prompt", "A story", "--style", "custom-style"])
        assert result.exit_code == 0
        mock_gen.assert_called_once()
        assert mock_gen.call_args[1].get("style_guide_name") or mock_gen.call_args[0][1] == "custom-style"
        state = json.loads((tmp_path / "books" / "test-book" / "state.json").read_text())
        assert state["style_guide"] == "custom-style"

    @patch("bookforge.cli.new.generate_story", return_value=SAMPLE_STORY)
    def test_custom_page_count(self, mock_gen, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """--pages option is passed to generate_story."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["new", "test-book", "--prompt", "A story", "--pages", "8"])
        assert result.exit_code == 0
        mock_gen.assert_called_once()
        call_kwargs = mock_gen.call_args
        # page_count should be 8 either as kwarg or positional
        assert call_kwargs.kwargs.get("page_count") == 8 or (len(call_kwargs.args) > 2 and call_kwargs.args[2] == 8)
