"""PDF export via WeasyPrint with FontConfiguration for Korean text support.

Renders an HTML string to PDF. For print format, delegates to postprocess
module for TrimBox/BleedBox/ICC injection.
"""

from pathlib import Path

from weasyprint import CSS, HTML
from weasyprint.text.fonts import FontConfiguration

from bookforge.build.postprocess import patch_print_pdf

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"


def build_pdf(
    html_string: str,
    output_path: Path,
    fmt: str,
    trim_inches: tuple[float, float],
    bleed_inches: float,
    book_dir: Path,
) -> Path:
    """Render HTML string to PDF via WeasyPrint.

    Args:
        html_string: Complete HTML document string.
        output_path: Where to write the PDF file.
        fmt: "screen" or "print".
        trim_inches: (width, height) trim size in inches.
        bleed_inches: Bleed size in inches (used for print post-processing).
        book_dir: Book project directory (used as base_url for relative paths).

    Returns:
        The output_path for chaining convenience.
    """
    font_config = FontConfiguration()

    # Build @font-face CSS with absolute path to bundled Noto Sans KR
    font_path = (FONTS_DIR / "NotoSansKR-Regular.otf").resolve().as_uri()
    font_css = CSS(
        string=f"""
        @font-face {{
            font-family: 'Noto Sans KR';
            src: url('{font_path}') format('opentype');
            font-weight: normal;
            font-style: normal;
        }}
        """,
        font_config=font_config,
    )

    html_doc = HTML(string=html_string, base_url=str(book_dir))
    html_doc.write_pdf(
        str(output_path),
        stylesheets=[font_css],
        font_config=font_config,
        optimize_images=True,
    )

    # Post-process print PDFs for KDP compliance
    if fmt == "print":
        patch_print_pdf(output_path, trim_inches, bleed_inches)

    return output_path
