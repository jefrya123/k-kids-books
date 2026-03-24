"""Tests for bookforge.publish.covers -- cover image generation and spine width."""

import pytest
from pathlib import Path
from PIL import Image


def _make_test_cover(tmp_path: Path) -> Path:
    """Create a simple 1024x1024 test cover image."""
    cover = tmp_path / "cover.png"
    img = Image.new("RGB", (1024, 1024), color=(100, 150, 200))
    img.save(cover)
    return cover


class TestSpineWidth:
    def test_12_pages(self):
        from bookforge.publish.covers import compute_spine_width

        result = compute_spine_width(12)
        assert result == pytest.approx(0.027024)

    def test_100_pages(self):
        from bookforge.publish.covers import compute_spine_width

        result = compute_spine_width(100)
        assert result == pytest.approx(0.2252)


class TestKdpCoverDimensions:
    def test_8_5_square_trim_thin_spine(self):
        from bookforge.publish.covers import compute_kdp_cover_dimensions

        spine = 0.027024
        total_w, total_h = compute_kdp_cover_dimensions(8.5, 8.5, spine)
        # total_w = 2*8.5 + 0.027024 + 2*0.125 = 17.277024
        # total_h = 8.5 + 2*0.125 = 8.75
        assert total_w == pytest.approx(17.277024)
        assert total_h == pytest.approx(8.75)


class TestGumroadThumb:
    def test_creates_1600x2560(self, tmp_path):
        from bookforge.publish.covers import generate_gumroad_thumb

        cover = _make_test_cover(tmp_path)
        output = tmp_path / "gumroad-thumb.png"
        result = generate_gumroad_thumb(cover, output)
        assert result == output
        assert output.exists()
        img = Image.open(output)
        assert img.size == (1600, 2560)


class TestSocialSquare:
    def test_creates_1080x1080(self, tmp_path):
        from bookforge.publish.covers import generate_social_square

        cover = _make_test_cover(tmp_path)
        output = tmp_path / "social-square.png"
        result = generate_social_square(cover, output)
        assert result == output
        assert output.exists()
        img = Image.open(output)
        assert img.size == (1080, 1080)


class TestKdpCover:
    def test_creates_correct_dimensions(self, tmp_path):
        from bookforge.publish.covers import (
            compute_spine_width,
            compute_kdp_cover_dimensions,
            generate_kdp_cover,
        )

        cover = _make_test_cover(tmp_path)
        output = tmp_path / "kdp-cover.png"
        page_count = 12
        trim_w, trim_h = 8.5, 8.5
        dpi = 300

        result = generate_kdp_cover(cover, trim_w, trim_h, page_count, output, dpi=dpi)
        assert result == output
        assert output.exists()

        spine = compute_spine_width(page_count)
        expected_w, expected_h = compute_kdp_cover_dimensions(trim_w, trim_h, spine)
        expected_w_px = round(expected_w * dpi)
        expected_h_px = round(expected_h * dpi)

        img = Image.open(output)
        assert abs(img.size[0] - expected_w_px) <= 1
        assert abs(img.size[1] - expected_h_px) <= 1
