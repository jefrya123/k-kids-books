"""Tests for Pydantic story and style schemas."""

import pytest
from pydantic import ValidationError


# --- Story schema tests ---


class TestBilingualText:
    def test_valid(self):
        from bookforge.story.schema import BilingualText

        bt = BilingualText(en="Hello", ko="안녕하세요")
        assert bt.en == "Hello"
        assert bt.ko == "안녕하세요"


class TestBookMeta:
    def test_valid_frontmatter(self):
        from bookforge.story.schema import BookMeta

        meta = BookMeta(
            title="The Story of Dangun",
            title_ko="단군 이야기",
            slug="dangun-story",
            price=4.99,
            ages="4-8",
            style_guide="korean-cute-watercolor",
        )
        assert meta.title == "The Story of Dangun"
        assert meta.trim_size == "8.5x8.5"  # default

    def test_missing_title_raises(self):
        from bookforge.story.schema import BookMeta

        with pytest.raises(ValidationError):
            BookMeta(
                title_ko="단군 이야기",
                slug="dangun-story",
                price=4.99,
                ages="4-8",
                style_guide="korean-cute-watercolor",
            )


class TestPage:
    def test_valid_page(self):
        from bookforge.story.schema import Page, BilingualText

        page = Page(
            number=1,
            text=BilingualText(en="Hello", ko="안녕"),
            image_prompt="A sunny day",
        )
        assert page.number == 1
        assert page.image_override is None

    def test_empty_image_prompt_raises(self):
        from bookforge.story.schema import Page, BilingualText

        with pytest.raises(ValidationError):
            Page(
                number=1,
                text=BilingualText(en="Hello", ko="안녕"),
                image_prompt="",
            )

    def test_effective_prompt_returns_image_prompt(self):
        from bookforge.story.schema import Page, BilingualText

        page = Page(
            number=1,
            text=BilingualText(en="Hello", ko="안녕"),
            image_prompt="Original prompt",
        )
        assert page.effective_prompt() == "Original prompt"

    def test_effective_prompt_returns_override_when_set(self):
        from bookforge.story.schema import Page, BilingualText

        page = Page(
            number=1,
            text=BilingualText(en="Hello", ko="안녕"),
            image_prompt="Original prompt",
            image_override="Better prompt",
        )
        assert page.effective_prompt() == "Better prompt"


class TestBook:
    def test_empty_pages_raises(self):
        from bookforge.story.schema import Book, BookMeta

        meta = BookMeta(
            title="Test",
            title_ko="테스트",
            slug="test",
            price=4.99,
            ages="4-8",
            style_guide="test-style",
        )
        with pytest.raises(ValidationError, match="at least one page"):
            Book(meta=meta, pages=[])

    def test_valid_book(self):
        from bookforge.story.schema import Book, BookMeta, Page, BilingualText

        meta = BookMeta(
            title="Test",
            title_ko="테스트",
            slug="test",
            price=4.99,
            ages="4-8",
            style_guide="test-style",
        )
        page = Page(
            number=1,
            text=BilingualText(en="Hello", ko="안녕"),
            image_prompt="A scene",
        )
        book = Book(meta=meta, pages=[page])
        assert len(book.pages) == 1


# --- Style schema tests ---


class TestCharacterDef:
    def test_valid_character(self):
        from bookforge.style.schema import CharacterDef

        char = CharacterDef(
            name_en="Ho-rang",
            name_ko="호랑",
            description="A friendly tiger cub",
            reference_image="characters/horang-ref.png",
        )
        assert char.name_en == "Ho-rang"
        assert char.name_ko == "호랑"


class TestArtStyle:
    def test_valid(self):
        from bookforge.style.schema import ArtStyle

        style = ArtStyle(
            prompt_prefix="Cute watercolor",
            negative_prompt="dark, scary",
            color_palette=["#FFB5C2", "#B5D8FF"],
        )
        assert style.prompt_prefix == "Cute watercolor"


class TestImageConfig:
    def test_defaults_to_flux_kontext(self):
        from bookforge.style.schema import ImageConfig

        config = ImageConfig()
        assert config.provider == "flux_kontext_pro"
        assert config.width == 1024
        assert config.height == 1024


class TestStyleGuide:
    def test_valid_style_guide(self, sample_style_dict):
        from bookforge.style.schema import StyleGuide

        guide = StyleGuide(**sample_style_dict)
        assert guide.name == "korean-cute-watercolor"
        assert "ho-rang" in guide.characters
        assert "gom-i" in guide.characters

    def test_missing_art_style_raises(self, sample_style_dict):
        from bookforge.style.schema import StyleGuide

        del sample_style_dict["art_style"]
        with pytest.raises(ValidationError):
            StyleGuide(**sample_style_dict)

    def test_build_prompt_prefix(self, sample_style_dict):
        from bookforge.style.schema import StyleGuide

        guide = StyleGuide(**sample_style_dict)
        prefix = guide.build_prompt_prefix()
        assert isinstance(prefix, str)
        assert guide.art_style.prompt_prefix in prefix
        assert "Ho-rang" in prefix
        assert "Gom-i" in prefix

    def test_layout_defaults(self):
        from bookforge.style.schema import Layout

        layout = Layout()
        assert layout.trim_inches == [8.5, 8.5]
        assert layout.bleed_inches == 0.125
        assert layout.dpi == 300
