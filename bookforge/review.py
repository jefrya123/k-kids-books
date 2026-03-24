"""Review logic: gather book summary stats and provide review checklist."""

from __future__ import annotations

from pathlib import Path

from rich.table import Table

from bookforge.story.schema import Book

REVIEW_CHECKLIST: list[str] = [
    "Story reads naturally in English",
    "Korean translation proofread by native speaker",
    "All illustrations show consistent character design",
    "Cover image is strong and eye-catching",
    "No placeholder text or TODO markers remain",
]


def gather_summary(book: Book, book_dir: Path) -> dict:
    """Gather summary statistics for a book.

    Returns dict with: page_count, image_count, word_count_en,
    word_count_ko, pdf_files (list of dicts with name + size_kb).
    """
    page_count = len(book.pages)

    # Count page images (page-*.png pattern)
    images_dir = book_dir / "images"
    if images_dir.exists():
        image_count = len(list(images_dir.glob("page-*.png")))
    else:
        image_count = 0

    # Word counts across all pages
    word_count_en = sum(len(page.text.en.split()) for page in book.pages)
    word_count_ko = sum(len(page.text.ko.split()) for page in book.pages)

    # PDF files with sizes
    output_dir = book_dir / "output"
    pdf_files: list[dict] = []
    if output_dir.exists():
        for pdf in sorted(output_dir.glob("*.pdf")):
            pdf_files.append(
                {
                    "name": pdf.name,
                    "size_kb": round(pdf.stat().st_size / 1024, 1),
                }
            )

    return {
        "page_count": page_count,
        "image_count": image_count,
        "word_count_en": word_count_en,
        "word_count_ko": word_count_ko,
        "pdf_files": pdf_files,
    }


def format_summary(summary: dict) -> Table:
    """Format summary dict into a Rich Table for display."""
    table = Table(title="Book Review Summary")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    table.add_row("Pages", str(summary["page_count"]))
    table.add_row("Images", str(summary["image_count"]))
    table.add_row("EN word count", str(summary["word_count_en"]))
    table.add_row("KR word count", str(summary["word_count_ko"]))

    return table
