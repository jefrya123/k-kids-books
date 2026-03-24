"""Parse story.md files into validated Book models.

Reads YAML frontmatter via python-frontmatter, splits the body on
``## Page N`` headers, and extracts English text, Korean text,
image prompts, and optional image overrides from each section.

Critical: _extract_en() uses targeted removal of known structured
comments only -- it does NOT strip all HTML comments (Pitfall 1).
"""

import re
from pathlib import Path

import frontmatter

from bookforge.story.schema import BilingualText, Book, BookMeta, Page

# Patterns for structured comments (used for targeted removal in EN extraction)
_KO_BLOCK_RE = re.compile(r"<!--\s*ko\s*-->.*?<!--\s*/ko\s*-->", re.DOTALL)
_IMAGE_RE = re.compile(r"<!--\s*image:\s*(.*?)\s*-->", re.DOTALL)
_IMAGE_OVERRIDE_RE = re.compile(r"<!--\s*image-override:\s*(.*?)\s*-->", re.DOTALL)

# Page header splitter
_PAGE_HEADER_RE = re.compile(r"^## Page \d+\s*$", re.MULTILINE)


def parse_story(path: str | Path) -> Book:
    """Parse a story.md file into a validated Book model.

    Args:
        path: Path to the story.md file.

    Returns:
        A validated Book instance.

    Raises:
        pydantic.ValidationError: If frontmatter is missing required fields
            or the book has no pages.
    """
    post = frontmatter.load(str(path))
    meta = BookMeta(**post.metadata)

    # Split on ## Page N headers; first element is pre-header content (discard)
    sections = _PAGE_HEADER_RE.split(post.content)
    sections = [s.strip() for s in sections if s.strip()]

    pages = []
    for i, section in enumerate(sections, start=1):
        pages.append(
            Page(
                number=i,
                text=BilingualText(
                    en=_extract_en(section),
                    ko=_extract_ko(section),
                ),
                image_prompt=_extract_image(section),
                image_override=_extract_image_override(section),
            )
        )

    return Book(meta=meta, pages=pages)


def _extract_en(text: str) -> str:
    """Extract English text by removing only known structured comments.

    Preserves any regular HTML comments that appear in English prose
    (Pitfall 1 from research). Only removes:
    - <!-- ko -->...<!-- /ko --> blocks
    - <!-- image: ... --> comments
    - <!-- image-override: ... --> comments
    """
    clean = _KO_BLOCK_RE.sub("", text)
    clean = _IMAGE_RE.sub("", clean)
    clean = _IMAGE_OVERRIDE_RE.sub("", clean)
    # Collapse multiple blank lines into one, then strip
    clean = re.sub(r"\n{3,}", "\n\n", clean)
    return clean.strip()


def _extract_ko(text: str) -> str:
    """Extract Korean text from <!-- ko -->...<!-- /ko --> block."""
    match = re.search(r"<!--\s*ko\s*-->(.*?)<!--\s*/ko\s*-->", text, re.DOTALL)
    return match.group(1).strip() if match else ""


def _extract_image(text: str) -> str:
    """Extract image prompt from <!-- image: ... --> comment."""
    match = _IMAGE_RE.search(text)
    return match.group(1).strip() if match else ""


def _extract_image_override(text: str) -> str | None:
    """Extract image override from <!-- image-override: ... --> comment."""
    match = _IMAGE_OVERRIDE_RE.search(text)
    return match.group(1).strip() if match else None
