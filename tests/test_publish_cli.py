"""Tests for bookforge publish package orchestration and CLI command."""

import json
import zipfile
from pathlib import Path

import pytest
from PIL import Image

from bookforge.story.schema import BilingualText, Book, BookMeta, Page


def _make_test_book_dir(tmp_path: Path) -> Path:
    """Create a full test book directory with state, story, PDFs, and cover."""
    book_dir = tmp_path / "books" / "test-book"
    book_dir.mkdir(parents=True)

    # state.json with review approved
    state = {
        "review_approved": True,
        "review_date": "2026-03-24T12:00:00",
        "review_summary": {"page_count": 12, "image_count": 12},
    }
    (book_dir / "state.json").write_text(json.dumps(state))

    # story.md
    story = """---
title: "Test Book"
title_ko: "테스트 책"
slug: test-book
trim_size: "8.5x8.5"
price: 9.99
ages: "3-7"
style_guide: watercolor
---

## Page 1

Hello world

<!-- ko -->
안녕 세상
<!-- /ko -->

<!-- image: A friendly tiger -->
"""
    (book_dir / "story.md").write_text(story)

    # Fake PDFs in output/
    output_dir = book_dir / "output"
    output_dir.mkdir()
    for name in ["test-book-bilingual-screen.pdf", "test-book-bilingual-print.pdf"]:
        (output_dir / name).write_text("fake pdf content")

    # Cover image in images/
    images_dir = book_dir / "images"
    images_dir.mkdir()
    cover = Image.new("RGB", (1024, 1024), color=(100, 150, 200))
    cover.save(images_dir / "cover.png")

    return book_dir


class TestPublishRefusesWithoutApproval:
    def test_refuses_without_review(self, tmp_path):
        from bookforge.publish.package import create_publish_package
        from bookforge.story.parser import parse_story

        book_dir = _make_test_book_dir(tmp_path)
        # Remove approval
        state = json.loads((book_dir / "state.json").read_text())
        state["review_approved"] = False
        (book_dir / "state.json").write_text(json.dumps(state))

        book = parse_story(book_dir / "story.md")

        with pytest.raises(RuntimeError, match="not approved"):
            create_publish_package(book, book_dir)


class TestPublishPackage:
    def test_creates_full_package(self, tmp_path):
        from bookforge.publish.package import create_publish_package
        from bookforge.story.parser import parse_story

        book_dir = _make_test_book_dir(tmp_path)
        book = parse_story(book_dir / "story.md")

        result = create_publish_package(book, book_dir)
        pkg = book_dir / "publish-package"

        assert result == pkg
        assert pkg.exists()

        # PDFs copied
        pdfs = list(pkg.glob("*.pdf"))
        assert len(pdfs) == 2

        # Cover images
        assert (pkg / "gumroad-thumb.png").exists()
        assert (pkg / "social-square.png").exists()
        assert (pkg / "kdp-cover.png").exists()

        # Check image sizes
        thumb = Image.open(pkg / "gumroad-thumb.png")
        assert thumb.size == (1600, 2560)
        social = Image.open(pkg / "social-square.png")
        assert social.size == (1080, 1080)

        # Listing copy and checklist
        assert (pkg / "LISTING-COPY.md").exists()
        assert (pkg / "UPLOAD-CHECKLIST.md").exists()

        listing_text = (pkg / "LISTING-COPY.md").read_text()
        assert "Test Book" in listing_text
        assert "AI" in listing_text

        checklist_text = (pkg / "UPLOAD-CHECKLIST.md").read_text()
        assert "AI Content Disclosure" in checklist_text

    def test_creates_zip(self, tmp_path):
        from bookforge.publish.package import create_publish_package
        from bookforge.story.parser import parse_story

        book_dir = _make_test_book_dir(tmp_path)
        book = parse_story(book_dir / "story.md")

        create_publish_package(book, book_dir)

        zip_path = book_dir / "publish-package.zip"
        assert zip_path.exists()

        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            assert any("gumroad-thumb.png" in n for n in names)
            assert any("LISTING-COPY.md" in n for n in names)
            assert any("UPLOAD-CHECKLIST.md" in n for n in names)
            assert any(".pdf" in n for n in names)


class TestPublishCLI:
    def test_cli_refuses_without_approval(self, tmp_path):
        from typer.testing import CliRunner
        from bookforge.cli import app

        book_dir = _make_test_book_dir(tmp_path)
        state = json.loads((book_dir / "state.json").read_text())
        state["review_approved"] = False
        (book_dir / "state.json").write_text(json.dumps(state))

        runner = CliRunner()
        result = runner.invoke(app, ["publish", "test-book", "--books-dir", str(tmp_path / "books")])
        assert result.exit_code != 0
        assert "not approved" in result.output.lower()
