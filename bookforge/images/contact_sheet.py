"""HTML contact sheet generator with Pillow thumbnails."""

from __future__ import annotations

import base64
import io
from pathlib import Path

from PIL import Image

THUMB_SIZE = (300, 300)


def generate_contact_sheet(book_dir: Path, page_image_paths: list[Path]) -> Path:
    """Generate an HTML contact sheet with base64-embedded thumbnails.

    Returns the path to the generated HTML file.
    """
    output_path = book_dir / "images" / "contact-sheet.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not page_image_paths:
        output_path.write_text(_empty_html(book_dir.name))
        return output_path

    cards = []
    for img_path in page_image_paths:
        b64 = _thumbnail_base64(img_path)
        label = img_path.stem
        cards.append(
            f'<div class="card">'
            f'<img src="data:image/png;base64,{b64}" alt="{label}">'
            f'<p>{label}</p>'
            f'</div>'
        )

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Contact Sheet - {book_dir.name}</title>
<style>
body {{ font-family: sans-serif; padding: 20px; }}
h1 {{ color: #333; }}
.grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }}
.card {{ text-align: center; }}
.card img {{ max-width: 100%; border: 1px solid #ddd; border-radius: 4px; }}
.card p {{ margin-top: 4px; font-size: 14px; color: #666; }}
</style>
</head>
<body>
<h1>{book_dir.name}</h1>
<div class="grid">
{"".join(cards)}
</div>
</body>
</html>"""

    output_path.write_text(html)
    return output_path


def _thumbnail_base64(image_path: Path) -> str:
    """Open image, thumbnail to THUMB_SIZE, return base64 PNG string."""
    img = Image.open(image_path)
    img.thumbnail(THUMB_SIZE)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _empty_html(title: str) -> str:
    """HTML for empty contact sheet."""
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Contact Sheet - {title}</title>
</head>
<body>
<h1>{title}</h1>
<p>No images generated yet.</p>
</body>
</html>"""
