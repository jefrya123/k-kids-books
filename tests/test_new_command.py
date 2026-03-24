"""Tests for the bookforge new CLI command."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from bookforge.cli import app

runner = CliRunner()


class TestNewCommand:
    """Tests for bookforge new subcommand (scaffold-only, no API calls)."""

    def test_creates_book_directory(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """new command creates books/<slug>/ directory."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["new", "test-book"])
        assert result.exit_code == 0
        assert (tmp_path / "books" / "test-book").is_dir()

    def test_creates_subdirectories(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """new command creates images/, dist/, publish/ subdirectories."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["new", "test-book"])
        assert result.exit_code == 0
        book_dir = tmp_path / "books" / "test-book"
        assert (book_dir / "images").is_dir()
        assert (book_dir / "dist").is_dir()
        assert (book_dir / "publish").is_dir()

    def test_writes_story_template(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """new command writes story.md with template containing page boundaries."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["new", "test-book"])
        assert result.exit_code == 0
        story_file = tmp_path / "books" / "test-book" / "story.md"
        assert story_file.exists()
        content = story_file.read_text()
        assert "## Page 1" in content
        assert "## Page 2-3" in content
        assert "<!-- ko -->" in content
        assert "<!-- image:" in content
        assert 'slug: test-book' in content

    def test_title_in_template(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """--title option sets title in story.md frontmatter."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["new", "dangun", "--title", "The Story of Dangun"])
        assert result.exit_code == 0
        content = (tmp_path / "books" / "dangun" / "story.md").read_text()
        assert 'title: "The Story of Dangun"' in content

    def test_default_title_from_slug(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Without --title, title defaults to slug converted to title case."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["new", "admiral-yi"])
        assert result.exit_code == 0
        content = (tmp_path / "books" / "admiral-yi" / "story.md").read_text()
        assert 'title: "Admiral Yi"' in content

    def test_writes_state_json(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """new command writes state.json with correct initial state."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["new", "test-book"])
        assert result.exit_code == 0
        state_file = tmp_path / "books" / "test-book" / "state.json"
        assert state_file.exists()
        state = json.loads(state_file.read_text())
        assert state["slug"] == "test-book"
        assert state["style_guide"] == "korean-cute-watercolor"
        assert state["stages"]["story"] == "pending"
        assert state["stages"]["illustrate"] == "pending"

    def test_error_on_existing_slug(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """new command exits with error if book directory already exists."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "books" / "test-book").mkdir(parents=True)
        result = runner.invoke(app, ["new", "test-book"])
        assert result.exit_code == 1

    def test_new_subcommand_registered(self) -> None:
        """bookforge --help shows 'new' subcommand."""
        result = runner.invoke(app, ["--help"])
        assert "new" in result.output

    def test_custom_style_guide(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """--style option is saved in state.json."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["new", "test-book", "--style", "custom-style"])
        assert result.exit_code == 0
        state = json.loads((tmp_path / "books" / "test-book" / "state.json").read_text())
        assert state["style_guide"] == "custom-style"
