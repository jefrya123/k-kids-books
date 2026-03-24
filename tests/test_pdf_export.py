"""Tests for PDF export (build_pdf) and print post-processing (patch_print_pdf)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pikepdf
import pytest


@pytest.fixture
def tmp_pdf(tmp_path: Path) -> Path:
    """Create a minimal PDF via WeasyPrint for testing."""
    from weasyprint import HTML

    pdf_path = tmp_path / "test.pdf"
    HTML(string="<html><body><p>hello</p></body></html>").write_pdf(str(pdf_path))
    return pdf_path


class TestBuildPdf:
    """Tests for build_pdf() function."""

    def test_build_pdf_screen_creates_file(self, tmp_path: Path) -> None:
        """build_pdf() with format='screen' produces a PDF file at the output path."""
        from bookforge.build.pdf import build_pdf

        html = "<html><body><p>test</p></body></html>"
        out = tmp_path / "out.pdf"
        result = build_pdf(
            html_string=html,
            output_path=out,
            fmt="screen",
            trim_inches=(8.5, 8.5),
            bleed_inches=0.125,
            book_dir=tmp_path,
        )
        assert result == out
        assert out.exists()
        assert out.stat().st_size > 0

    def test_build_pdf_passes_font_config_to_css_and_write_pdf(
        self, tmp_path: Path
    ) -> None:
        """build_pdf() passes FontConfiguration to both CSS() and write_pdf()."""
        from bookforge.build.pdf import build_pdf

        with (
            patch("bookforge.build.pdf.CSS") as mock_css,
            patch("bookforge.build.pdf.HTML") as mock_html,
            patch("bookforge.build.pdf.FontConfiguration") as mock_fc,
        ):
            mock_fc_instance = MagicMock()
            mock_fc.return_value = mock_fc_instance
            mock_css_instance = MagicMock()
            mock_css.return_value = mock_css_instance
            mock_html_instance = MagicMock()
            mock_html.return_value = mock_html_instance
            mock_html_instance.write_pdf.return_value = None

            out = tmp_path / "out.pdf"
            build_pdf(
                html_string="<html><body>test</body></html>",
                output_path=out,
                fmt="screen",
                trim_inches=(8.5, 8.5),
                bleed_inches=0.125,
                book_dir=tmp_path,
            )

            # CSS() must receive font_config
            mock_css.assert_called()
            for call in mock_css.call_args_list:
                assert call.kwargs.get("font_config") is mock_fc_instance

            # write_pdf() must receive font_config
            mock_html_instance.write_pdf.assert_called_once()
            write_call = mock_html_instance.write_pdf.call_args
            assert write_call.kwargs.get("font_config") is mock_fc_instance

    def test_screen_pdf_not_postprocessed(self, tmp_path: Path) -> None:
        """Screen PDFs do NOT get our custom post-processing (no ICC OutputIntent)."""
        from bookforge.build.pdf import build_pdf

        html = "<html><body><p>screen test</p></body></html>"
        out = tmp_path / "screen.pdf"
        build_pdf(
            html_string=html,
            output_path=out,
            fmt="screen",
            trim_inches=(8.5, 8.5),
            bleed_inches=0.125,
            book_dir=tmp_path,
        )

        with pikepdf.open(out) as pdf:
            # Screen PDFs must not have our custom sRGB OutputIntent
            assert "/OutputIntents" not in pdf.Root


class TestPatchPrintPdf:
    """Tests for patch_print_pdf() function."""

    def test_sets_trimbox_and_bleedbox(self, tmp_pdf: Path) -> None:
        """patch_print_pdf() sets TrimBox and BleedBox on all pages."""
        from bookforge.build.postprocess import patch_print_pdf

        patch_print_pdf(tmp_pdf, trim_inches=(8.5, 8.5), bleed_inches=0.125)

        with pikepdf.open(tmp_pdf) as pdf:
            for page in pdf.pages:
                assert "/TrimBox" in page
                assert "/BleedBox" in page
                assert "/MediaBox" in page

    def test_embeds_icc_output_intent(self, tmp_pdf: Path) -> None:
        """patch_print_pdf() embeds an OutputIntent with sRGB ICC profile."""
        from bookforge.build.postprocess import patch_print_pdf

        patch_print_pdf(tmp_pdf, trim_inches=(8.5, 8.5), bleed_inches=0.125)

        with pikepdf.open(tmp_pdf) as pdf:
            assert "/OutputIntents" in pdf.Root
            intents = pdf.Root["/OutputIntents"]
            assert len(intents) >= 1
            intent = intents[0]
            assert str(intent["/S"]) == "/GTS_PDFA1"
            assert "/DestOutputProfile" in intent

    def test_correct_box_dimensions_8_5_square(self, tmp_pdf: Path) -> None:
        """For 8.5x8.5 trim + 0.125 bleed: MediaBox=[0,0,630,630], TrimBox=[9,9,621,621]."""
        from bookforge.build.postprocess import patch_print_pdf

        patch_print_pdf(tmp_pdf, trim_inches=(8.5, 8.5), bleed_inches=0.125)

        with pikepdf.open(tmp_pdf) as pdf:
            page = pdf.pages[0]
            media = [float(v) for v in page["/MediaBox"]]
            trim = [float(v) for v in page["/TrimBox"]]
            bleed = [float(v) for v in page["/BleedBox"]]

            # MediaBox: (8.5 + 2*0.125) * 72 = 630
            assert media == [0, 0, 630, 630]
            # TrimBox: bleed_pt=9 inset from media edges
            assert trim == [9, 9, 621, 621]
            # BleedBox = MediaBox
            assert bleed == [0, 0, 630, 630]

    def test_dimensions_computed_from_parameters(self, tmp_pdf: Path) -> None:
        """Dimensions are computed from parameters, not hardcoded."""
        from bookforge.build.postprocess import patch_print_pdf

        # Non-standard size: 6x9 trim, 0.25 bleed
        patch_print_pdf(tmp_pdf, trim_inches=(6.0, 9.0), bleed_inches=0.25)

        with pikepdf.open(tmp_pdf) as pdf:
            page = pdf.pages[0]
            media = [float(v) for v in page["/MediaBox"]]
            trim = [float(v) for v in page["/TrimBox"]]

            # MediaBox: (6+0.5)*72=468, (9+0.5)*72=684
            assert media == [0, 0, 468, 684]
            # TrimBox: bleed_pt = 0.25*72 = 18
            assert trim == [18, 18, 450, 666]
