"""Tests for the CLI review command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from bookforge.cli import app

runner = CliRunner()


@pytest.fixture
def mock_book_dir(tmp_path: Path, monkeypatch) -> Path:
    """Set up a fake books/ directory with story.md and assets for review."""
    books_dir = tmp_path / "books"
    book_dir = books_dir / "test-book"
    images_dir = book_dir / "images"
    images_dir.mkdir(parents=True)
    output_dir = book_dir / "output"
    output_dir.mkdir(parents=True)

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

    # Create some images
    (images_dir / "page-01.png").write_bytes(b"\x89PNG fake")

    # Create a PDF
    (output_dir / "test-book-bilingual-screen.pdf").write_bytes(b"x" * 2048)

    monkeypatch.chdir(tmp_path)
    return book_dir


class TestReviewCommand:
    """Tests for the review CLI command."""

    def test_approve_stamps_state(self, mock_book_dir: Path) -> None:
        """Answering 'y' stamps review_approved into state.json."""
        result = runner.invoke(app, ["review", "test-book"], input="y\n")
        assert result.exit_code == 0, result.output

        state = json.loads((mock_book_dir / "state.json").read_text())
        assert state["review_approved"] is True
        assert "review_date" in state
        assert "review_summary" in state

    def test_decline_no_approval(self, mock_book_dir: Path) -> None:
        """Answering 'n' does not stamp approval."""
        result = runner.invoke(app, ["review", "test-book"], input="n\n")
        assert result.exit_code == 0

        state_path = mock_book_dir / "state.json"
        if state_path.exists():
            state = json.loads(state_path.read_text())
            assert state.get("review_approved") is not True
        # If no state.json exists, that's also fine (no approval)

    def test_already_approved_shows_status(self, mock_book_dir: Path) -> None:
        """If already approved, shows status without re-prompting."""
        # Pre-stamp approval
        state = {
            "review_approved": True,
            "review_date": "2026-03-24T12:00:00",
            "review_summary": {"page_count": 1},
        }
        (mock_book_dir / "state.json").write_text(json.dumps(state))

        result = runner.invoke(app, ["review", "test-book"])
        assert result.exit_code == 0
        assert "already approved" in result.output.lower()

    def test_missing_book_dir_exits_1(self, tmp_path: Path, monkeypatch) -> None:
        """Missing book directory returns exit code 1."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["review", "nonexistent-book"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower() or "error" in result.output.lower()

    def test_prints_summary_info(self, mock_book_dir: Path) -> None:
        """Command prints summary stats."""
        result = runner.invoke(app, ["review", "test-book"], input="n\n")
        assert result.exit_code == 0
        # Should contain stats somewhere in output
        assert "page" in result.output.lower() or "image" in result.output.lower()

    def test_prints_checklist(self, mock_book_dir: Path) -> None:
        """Command prints checklist items."""
        result = runner.invoke(app, ["review", "test-book"], input="n\n")
        assert result.exit_code == 0
        assert "checklist" in result.output.lower() or "story reads" in result.output.lower()
