"""Print PDF post-processing via pikepdf.

Sets MediaBox/TrimBox/BleedBox and embeds sRGB ICC OutputIntent
for KDP print compliance.
"""

from pathlib import Path

import pikepdf

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
ICC_DIR = ASSETS_DIR / "icc"

PTS_PER_INCH = 72


def patch_print_pdf(
    pdf_path: Path,
    trim_inches: tuple[float, float],
    bleed_inches: float,
) -> None:
    """Post-process a PDF for print: set page boxes and embed sRGB ICC.

    Args:
        pdf_path: Path to PDF file (modified in place).
        trim_inches: (width, height) trim size in inches.
        bleed_inches: Bleed size in inches.
    """
    trim_w_pt = trim_inches[0] * PTS_PER_INCH
    trim_h_pt = trim_inches[1] * PTS_PER_INCH
    bleed_pt = bleed_inches * PTS_PER_INCH

    media_w = trim_w_pt + 2 * bleed_pt
    media_h = trim_h_pt + 2 * bleed_pt

    with pikepdf.open(pdf_path, allow_overwriting_input=True) as pdf:
        # Set page boxes on every page
        for page in pdf.pages:
            page["/MediaBox"] = [0, 0, media_w, media_h]
            page["/TrimBox"] = [bleed_pt, bleed_pt, media_w - bleed_pt, media_h - bleed_pt]
            page["/BleedBox"] = [0, 0, media_w, media_h]

        # Embed sRGB ICC OutputIntent
        _embed_srgb_output_intent(pdf)

        pdf.save(pdf_path, linearize=True)


def _embed_srgb_output_intent(pdf: pikepdf.Pdf) -> None:
    """Embed an sRGB ICC OutputIntent into the PDF catalog."""
    icc_path = ICC_DIR / "sRGB_v4_ICC_preference.icc"
    icc_data = icc_path.read_bytes()

    icc_stream = pikepdf.Stream(pdf, icc_data)
    icc_stream["/N"] = 3
    icc_stream["/Alternate"] = pikepdf.Name("/DeviceRGB")

    output_intent = pikepdf.Dictionary(
        {
            "/Type": pikepdf.Name("/OutputIntent"),
            "/S": pikepdf.Name("/GTS_PDFA1"),
            "/OutputConditionIdentifier": pikepdf.String("sRGB IEC61966-2.1"),
            "/DestOutputProfile": icc_stream,
        }
    )

    # Must make indirect before appending (pikepdf requirement)
    output_intent = pdf.make_indirect(output_intent)

    if "/OutputIntents" not in pdf.Root:
        pdf.Root["/OutputIntents"] = pikepdf.Array()
    pdf.Root["/OutputIntents"].append(output_intent)
