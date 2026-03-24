"""Tests for the CLI build command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from bookforge.cli import app

runner = CliRunner()


@pytest.fixture
def mock_book_dir(tmp_path: Path, monkeypatch):
    """Set up a fake books/ directory with story.md, style guide, and placeholder images."""
    books_dir = tmp_path / "books"
    book_dir = books_dir / "test-book"
    (book_dir / "images").mkdir(parents=True)

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

    monkeypatch.chdir(tmp_path)
    return book_dir


def _count_pdfs(book_dir: Path) -> int:
    """Count PDF files in the output directory."""
    output_dir = book_dir / "output"
    if not output_dir.exists():
        return 0
    return len(list(output_dir.glob("*.pdf")))


def _pdf_names(book_dir: Path) -> set[str]:
    """Get set of PDF filenames in the output directory."""
    output_dir = book_dir / "output"
    if not output_dir.exists():
        return set()
    return {f.name for f in output_dir.glob("*.pdf")}


class TestBuildCommand:
    """Tests for the build CLI command."""

    def test_default_builds_bilingual_screen_and_print(self, mock_book_dir: Path) -> None:
        """Default invocation produces bilingual screen + print (2 PDFs)."""
        result = runner.invoke(app, ["build", "test-book"])
        assert result.exit_code == 0, result.output
        names = _pdf_names(mock_book_dir)
        assert names == {"test-book-bilingual-screen.pdf", "test-book-bilingual-print.pdf"}

    def test_lang_all_builds_six_pdfs(self, mock_book_dir: Path) -> None:
        """`--lang all` builds 6 PDFs (3 editions x 2 formats)."""
        result = runner.invoke(app, ["build", "test-book", "--lang", "all"])
        assert result.exit_code == 0, result.output
        names = _pdf_names(mock_book_dir)
        expected = {
            "test-book-en-screen.pdf",
            "test-book-en-print.pdf",
            "test-book-ko-screen.pdf",
            "test-book-ko-print.pdf",
            "test-book-bilingual-screen.pdf",
            "test-book-bilingual-print.pdf",
        }
        assert names == expected

    def test_lang_en_builds_two_pdfs(self, mock_book_dir: Path) -> None:
        """`--lang en` builds 2 PDFs (en-screen, en-print)."""
        result = runner.invoke(app, ["build", "test-book", "--lang", "en"])
        assert result.exit_code == 0, result.output
        names = _pdf_names(mock_book_dir)
        assert names == {"test-book-en-screen.pdf", "test-book-en-print.pdf"}

    def test_lang_ko_format_screen_builds_one_pdf(self, mock_book_dir: Path) -> None:
        """`--lang ko --format screen` builds 1 PDF (ko-screen)."""
        result = runner.invoke(app, ["build", "test-book", "--lang", "ko", "--format", "screen"])
        assert result.exit_code == 0, result.output
        names = _pdf_names(mock_book_dir)
        assert names == {"test-book-ko-screen.pdf"}

    def test_missing_book_dir_exits_with_error(self, tmp_path: Path, monkeypatch) -> None:
        """Missing book directory returns exit code 1."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["build", "nonexistent-book"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_output_files_have_nonzero_size(self, mock_book_dir: Path) -> None:
        """Output PDFs exist with non-zero size."""
        result = runner.invoke(app, ["build", "test-book", "--lang", "en", "--format", "screen"])
        assert result.exit_code == 0, result.output
        pdf = mock_book_dir / "output" / "test-book-en-screen.pdf"
        assert pdf.exists()
        assert pdf.stat().st_size > 0

    def test_prints_summary(self, mock_book_dir: Path) -> None:
        """Command prints summary of generated files."""
        result = runner.invoke(app, ["build", "test-book", "--lang", "en", "--format", "screen"])
        assert result.exit_code == 0
        assert "test-book-en-screen.pdf" in result.output
