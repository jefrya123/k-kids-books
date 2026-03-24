"""Tests for Jinja2 templates, CSS, bundled assets, and render_book_html renderer."""

from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader

from bookforge.story.schema import BilingualText, Book, BookMeta, Page
from bookforge.style.schema import ArtStyle, ImageConfig, Layout, StyleGuide, CharacterDef

ASSETS_DIR = Path(__file__).resolve().parent.parent / "bookforge" / "assets"
TEMPLATES_DIR = ASSETS_DIR / "templates"
FONTS_DIR = ASSETS_DIR / "fonts"
ICC_DIR = ASSETS_DIR / "icc"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_book() -> Book:
    return Book(
        meta=BookMeta(
            title="Test Book",
            title_ko="테스트 북",
            slug="test-book",
            trim_size="8.5x8.5",
            price=9.99,
            ages="3-7",
            style_guide="test-style",
        ),
        pages=[
            Page(
                number=1,
                text=BilingualText(en="Hello world", ko="안녕하세요"),
                image_prompt="a sunny meadow",
            ),
            Page(
                number=2,
                text=BilingualText(en="Goodbye world", ko="안녕히 가세요"),
                image_prompt="a starry night",
            ),
        ],
    )


@pytest.fixture
def sample_style_guide() -> StyleGuide:
    return StyleGuide(
        name="test-style",
        art_style=ArtStyle(
            prompt_prefix="watercolor style",
            negative_prompt="photo, realistic",
            color_palette=["#FFD700", "#87CEEB"],
        ),
        characters={
            "hero": CharacterDef(
                name_en="Hero",
                name_ko="영웅",
                description="A brave child",
                reference_image="hero.png",
            )
        },
        layout=Layout(
            trim_inches=[8.5, 8.5],
            bleed_inches=0.125,
            safe_margin_inches=0.25,
            dpi=300,
        ),
    )


# ---------------------------------------------------------------------------
# Task 1: Bundled asset tests
# ---------------------------------------------------------------------------

class TestBundledAssets:
    def test_noto_sans_kr_font_exists(self):
        font_path = FONTS_DIR / "NotoSansKR-Regular.otf"
        assert font_path.exists(), f"Font not found at {font_path}"

    def test_noto_sans_kr_font_size(self):
        """Font must be > 1MB (real KR font, not placeholder)."""
        font_path = FONTS_DIR / "NotoSansKR-Regular.otf"
        assert font_path.stat().st_size > 1_000_000

    def test_srgb_icc_profile_exists(self):
        icc_path = ICC_DIR / "sRGB_v4_ICC_preference.icc"
        assert icc_path.exists(), f"ICC profile not found at {icc_path}"

    def test_srgb_icc_profile_size(self):
        """ICC profile must be > 1KB."""
        icc_path = ICC_DIR / "sRGB_v4_ICC_preference.icc"
        assert icc_path.stat().st_size > 1_000


# ---------------------------------------------------------------------------
# Task 1: CSS tests
# ---------------------------------------------------------------------------

class TestCSS:
    def test_base_css_has_font_face(self):
        css = (TEMPLATES_DIR / "css" / "base.css").read_text()
        assert "@font-face" in css
        assert "url(" in css
        assert "Noto Sans KR" in css

    def test_print_css_has_bleed(self):
        css = (TEMPLATES_DIR / "css" / "print.css").read_text()
        assert "bleed:" in css or "bleed :" in css
        assert "0.125in" in css or "{{ bleed }}in" in css
        assert "marks" in css

    def test_screen_css_no_bleed(self):
        css = (TEMPLATES_DIR / "css" / "screen.css").read_text()
        assert "bleed" not in css


# ---------------------------------------------------------------------------
# Task 1: Template edition-filtering tests
# ---------------------------------------------------------------------------

class TestTemplateEditionFiltering:
    """Test that book_page.html.j2 filters text by edition."""

    @pytest.fixture
    def jinja_env(self):
        return Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

    @pytest.fixture
    def render_ctx(self, sample_book):
        return dict(
            pages=sample_book.pages,
            image_dir="/tmp/images",
            font_path="/tmp/fonts/NotoSansKR-Regular.otf",
            trim_w=8.5,
            trim_h=8.5,
            page_w=8.5,
            page_h=8.5,
            bleed=0.0,
            safe_margin=0.25,
            base_url="/tmp",
        )

    def test_english_only_edition(self, jinja_env, render_ctx):
        tpl = jinja_env.get_template("book_page.html.j2")
        html = tpl.render(edition="en", **render_ctx)
        assert "Hello world" in html
        assert "안녕하세요" not in html

    def test_korean_only_edition(self, jinja_env, render_ctx):
        tpl = jinja_env.get_template("book_page.html.j2")
        html = tpl.render(edition="ko", **render_ctx)
        assert "안녕하세요" in html
        assert "Hello world" not in html

    def test_bilingual_edition(self, jinja_env, render_ctx):
        tpl = jinja_env.get_template("book_page.html.j2")
        html = tpl.render(edition="bilingual", **render_ctx)
        assert "Hello world" in html
        assert "안녕하세요" in html


# ---------------------------------------------------------------------------
# Task 2: render_book_html tests
# ---------------------------------------------------------------------------

class TestRenderBookHtml:
    def test_english_edition_screen(self, sample_book, sample_style_guide, tmp_path):
        from bookforge.build.renderer import render_book_html

        html = render_book_html(sample_book, "en", sample_style_guide, "screen", tmp_path)
        assert "Hello world" in html
        assert "Goodbye world" in html
        assert "안녕하세요" not in html
        assert "안녕히 가세요" not in html

    def test_korean_edition_screen(self, sample_book, sample_style_guide, tmp_path):
        from bookforge.build.renderer import render_book_html

        html = render_book_html(sample_book, "ko", sample_style_guide, "screen", tmp_path)
        assert "안녕하세요" in html
        assert "안녕히 가세요" in html
        assert "Hello world" not in html
        assert "Goodbye world" not in html

    def test_bilingual_edition_screen(self, sample_book, sample_style_guide, tmp_path):
        from bookforge.build.renderer import render_book_html

        html = render_book_html(sample_book, "bilingual", sample_style_guide, "screen", tmp_path)
        assert "Hello world" in html
        assert "안녕하세요" in html

    def test_print_format_has_bleed(self, sample_book, sample_style_guide, tmp_path):
        from bookforge.build.renderer import render_book_html

        html = render_book_html(sample_book, "en", sample_style_guide, "print", tmp_path)
        assert "bleed" in html or "0.125in" in html
        assert "marks" in html

    def test_screen_format_no_bleed(self, sample_book, sample_style_guide, tmp_path):
        from bookforge.build.renderer import render_book_html

        html = render_book_html(sample_book, "en", sample_style_guide, "screen", tmp_path)
        assert "bleed" not in html

    def test_dimensions_from_trim_size(self, sample_book, sample_style_guide, tmp_path):
        from bookforge.build.renderer import render_book_html

        html = render_book_html(sample_book, "en", sample_style_guide, "screen", tmp_path)
        # 8.5x8.5 trim size → page dimensions in CSS
        assert "8.5in" in html

    def test_custom_trim_size(self, sample_book, sample_style_guide, tmp_path):
        from bookforge.build.renderer import render_book_html

        sample_book.meta.trim_size = "6x9"
        html = render_book_html(sample_book, "en", sample_style_guide, "screen", tmp_path)
        assert "6.0in" in html or "6in" in html
        assert "9.0in" in html or "9in" in html
        # Should NOT have 8.5
        assert "8.5in" not in html
