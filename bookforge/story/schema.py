"""Pydantic models for story data: Book, BookMeta, Page, BilingualText."""

from pydantic import BaseModel, field_validator


class BilingualText(BaseModel):
    """A pair of English and Korean text."""

    en: str
    ko: str


class Page(BaseModel):
    """A single page in a book with bilingual text and image prompt."""

    number: int
    text: BilingualText
    image_prompt: str
    image_override: str | None = None

    @field_validator("image_prompt")
    @classmethod
    def image_prompt_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("image_prompt must not be empty")
        return v

    def effective_prompt(self) -> str:
        """Return override if set, else original prompt."""
        return self.image_override or self.image_prompt


class BookMeta(BaseModel):
    """YAML frontmatter metadata for a book."""

    title: str
    title_ko: str
    slug: str
    trim_size: str = "8.5x8.5"
    price: float
    ages: str
    style_guide: str


class Book(BaseModel):
    """A complete book with metadata and pages."""

    meta: BookMeta
    pages: list[Page]

    @field_validator("pages")
    @classmethod
    def must_have_pages(cls, v: list[Page]) -> list[Page]:
        if not v:
            raise ValueError("Book must have at least one page")
        return v
