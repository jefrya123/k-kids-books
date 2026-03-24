"""Tests for HTML contact sheet generator."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from bookforge.images.contact_sheet import generate_contact_sheet


@pytest.fixture
def sample_images(tmp_path: Path) -> list[Path]:
    """Create 3 small test PNG images."""
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    paths = []
    for i in range(1, 4):
        img = Image.new("RGB", (100, 100), color=(i * 50, i * 30, i * 70))
        path = images_dir / f"page-{i:02d}-v1.png"
        img.save(path, format="PNG")
        paths.append(path)
    return paths


@pytest.fixture
def book_dir_cs(tmp_path: Path) -> Path:
    """Book directory for contact sheet tests."""
    book = tmp_path / "test-book"
    (book / "images").mkdir(parents=True)
    return book


class TestContactSheet:
    def test_contact_sheet_written(self, book_dir_cs, sample_images):
        """Given 3 image paths, generates contact-sheet.html with base64 thumbnails."""
        result_path = generate_contact_sheet(book_dir_cs, sample_images)
        assert result_path.exists()
        assert result_path.name == "contact-sheet.html"
        content = result_path.read_text()
        assert "data:image/png;base64," in content

    def test_contact_sheet_html_structure(self, book_dir_cs, sample_images):
        """Output HTML contains img tags with base64 src for each page, page labels."""
        result_path = generate_contact_sheet(book_dir_cs, sample_images)
        content = result_path.read_text()
        # Should have 3 img tags
        assert content.count("<img") == 3
        # Should have page labels
        assert "page-01" in content
        assert "page-02" in content
        assert "page-03" in content

    def test_contact_sheet_empty(self, book_dir_cs):
        """With 0 images, generates HTML with 'No images generated' message."""
        result_path = generate_contact_sheet(book_dir_cs, [])
        assert result_path.exists()
        content = result_path.read_text()
        assert "No images generated" in content
