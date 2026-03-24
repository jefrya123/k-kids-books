"""Soft validator for Book completeness.

Returns warning strings (not exceptions) for pages missing
Korean text, English text, or image prompts. Used by the CLI
to show issues to the user before proceeding with illustration.
"""

from bookforge.story.schema import Book


def validate_book(book: Book) -> list[str]:
    """Check each page for completeness and return warning messages.

    Args:
        book: A parsed Book model.

    Returns:
        A list of warning strings. Empty list means the book is complete.
    """
    warnings: list[str] = []

    for page in book.pages:
        if not page.text.en.strip():
            warnings.append(f"Page {page.number}: missing English text")
        if not page.text.ko.strip():
            warnings.append(f"Page {page.number}: missing Korean text")
        if not page.image_prompt.strip():
            warnings.append(f"Page {page.number}: missing image prompt")

    return warnings
