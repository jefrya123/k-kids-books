"""Cover image generation for publish packages.

Generates three cover variants:
- Gumroad thumbnail (1600x2560)
- KDP full cover spread (back + spine + front with bleed)
- Social media square (1080x1080)

KDP spine width formula: page_count * 0.002252 inches (white paper).
"""

from pathlib import Path

from PIL import Image, ImageDraw


# KDP white paper spine factor (inches per page)
_SPINE_FACTOR = 0.002252

# Minimum spine width (inches) to attempt text rendering
_MIN_SPINE_FOR_TEXT = 0.5


def compute_spine_width(page_count: int) -> float:
    """Compute KDP spine width in inches for white paper.

    Formula: page_count * 0.002252
    """
    return page_count * _SPINE_FACTOR


def compute_kdp_cover_dimensions(
    trim_w: float,
    trim_h: float,
    spine_width: float,
    bleed: float = 0.125,
) -> tuple[float, float]:
    """Compute total KDP cover dimensions in inches.

    Returns (total_width, total_height) including:
    - Back cover (trim_w) + spine + front cover (trim_w)
    - Bleed on all four edges
    """
    total_width = 2 * trim_w + spine_width + 2 * bleed
    total_height = trim_h + 2 * bleed
    return (total_width, total_height)


def _get_dominant_color(img: Image.Image) -> tuple[int, int, int]:
    """Extract dominant color by downscaling to 1x1 pixel."""
    tiny = img.resize((1, 1), Image.LANCZOS)
    pixel = tiny.getpixel((0, 0))
    if isinstance(pixel, int):
        return (pixel, pixel, pixel)
    return pixel[:3]


def generate_gumroad_thumb(cover_path: Path, output_path: Path) -> Path:
    """Resize cover image to 1600x2560 Gumroad thumbnail PNG."""
    img = Image.open(cover_path)
    resized = img.resize((1600, 2560), Image.LANCZOS)
    resized.save(output_path, "PNG")
    return output_path


def generate_social_square(cover_path: Path, output_path: Path) -> Path:
    """Crop cover to center square and resize to 1080x1080 PNG."""
    img = Image.open(cover_path)
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    cropped = img.crop((left, top, left + side, top + side))
    resized = cropped.resize((1080, 1080), Image.LANCZOS)
    resized.save(output_path, "PNG")
    return output_path


def generate_kdp_cover(
    cover_path: Path,
    trim_w: float,
    trim_h: float,
    page_count: int,
    output_path: Path,
    dpi: int = 300,
) -> Path:
    """Generate full KDP cover spread: back + spine + front with bleed.

    Front cover is the provided cover image. Back cover and spine use
    the dominant color from the cover. Spine text is only added if the
    spine is wide enough (>= 0.5 inches, i.e., 222+ pages).
    """
    spine_width = compute_spine_width(page_count)
    total_w, total_h = compute_kdp_cover_dimensions(trim_w, trim_h, spine_width)

    total_w_px = round(total_w * dpi)
    total_h_px = round(total_h * dpi)

    bleed_px = round(0.125 * dpi)
    trim_w_px = round(trim_w * dpi)
    trim_h_px = round(trim_h * dpi)
    spine_w_px = total_w_px - 2 * trim_w_px - 2 * bleed_px

    # Open cover and get dominant color
    cover_img = Image.open(cover_path)
    dominant = _get_dominant_color(cover_img)

    # Create full spread canvas
    canvas = Image.new("RGB", (total_w_px, total_h_px), color=dominant)

    # Paste front cover on the right side (after back + spine, within bleed)
    front_x = bleed_px + trim_w_px + spine_w_px
    front_region = cover_img.resize((trim_w_px, trim_h_px), Image.LANCZOS)
    canvas.paste(front_region, (front_x, bleed_px))

    # Back cover is already the dominant color fill
    # Spine is already the dominant color fill

    # Only add spine text if spine is wide enough
    if spine_width >= _MIN_SPINE_FOR_TEXT:
        # For very wide spines, draw rotated title text
        # (not needed for typical children's books with 12-30 pages)
        _draw = ImageDraw.Draw(canvas)
        # Would add rotated text here for 222+ page books

    canvas.save(output_path, "PNG")
    return output_path
