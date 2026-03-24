"""Tests for bookforge.publish.listing -- listing copy and upload checklist."""

import pytest

from bookforge.story.schema import BilingualText, Book, BookMeta, Page


def _make_test_book() -> Book:
    """Create a minimal test book."""
    return Book(
        meta=BookMeta(
            title="Ho-rang's Big Day",
            title_ko="호랑이의 큰 날",
            slug="ho-rangs-big-day",
            trim_size="8.5x8.5",
            price=9.99,
            ages="3-7",
            style_guide="watercolor",
        ),
        pages=[
            Page(
                number=1,
                text=BilingualText(en="Hello world", ko="안녕 세상"),
                image_prompt="A tiger waving",
            ),
        ],
    )


class TestGenerateListingCopy:
    def test_returns_gumroad_and_kdp_keys(self):
        from bookforge.publish.listing import generate_listing_copy

        book = _make_test_book()
        result = generate_listing_copy(book, page_count=12)
        assert "gumroad" in result
        assert "kdp" in result

    def test_gumroad_structure(self):
        from bookforge.publish.listing import generate_listing_copy

        book = _make_test_book()
        result = generate_listing_copy(book, page_count=12)
        gumroad = result["gumroad"]
        assert "title" in gumroad
        assert "description" in gumroad
        assert "price" in gumroad
        assert gumroad["price"] == 9.99

    def test_kdp_structure(self):
        from bookforge.publish.listing import generate_listing_copy

        book = _make_test_book()
        result = generate_listing_copy(book, page_count=12)
        kdp = result["kdp"]
        assert "title" in kdp
        assert "subtitle" in kdp
        assert "description" in kdp
        assert "price" in kdp
        assert "keywords" in kdp
        assert len(kdp["keywords"]) == 7

    def test_ai_disclosure_in_descriptions(self):
        from bookforge.publish.listing import generate_listing_copy

        book = _make_test_book()
        result = generate_listing_copy(book, page_count=12)
        assert "AI" in result["gumroad"]["description"]
        assert "AI" in result["kdp"]["description"]

    def test_bilingual_mentioned(self):
        from bookforge.publish.listing import generate_listing_copy

        book = _make_test_book()
        result = generate_listing_copy(book, page_count=12)
        assert "bilingual" in result["gumroad"]["description"].lower()
        assert "bilingual" in result["kdp"]["description"].lower()


class TestRenderUploadChecklist:
    def test_renders_with_book_data(self):
        from bookforge.publish.listing import generate_listing_copy, render_upload_checklist

        book = _make_test_book()
        listing = generate_listing_copy(book, page_count=12)
        result = render_upload_checklist(book, listing, kdp_cover_dims=(17.28, 8.75))

        assert "Ho-rang's Big Day" in result
        assert "AI" in result
        assert "17.28" in result
        assert "8.75" in result
        assert "Gumroad" in result
        assert "KDP" in result

    def test_ai_disclosure_section(self):
        from bookforge.publish.listing import generate_listing_copy, render_upload_checklist

        book = _make_test_book()
        listing = generate_listing_copy(book, page_count=12)
        result = render_upload_checklist(book, listing, kdp_cover_dims=(17.28, 8.75))

        assert "AI Content Disclosure" in result
        assert "AI-generated content" in result
