"""Pydantic models for style guide: StyleGuide, CharacterDef, ArtStyle, ImageConfig, Layout."""

from pydantic import BaseModel


class CharacterDef(BaseModel):
    """A character definition with bilingual name, description, and reference image."""

    name_en: str
    name_ko: str
    description: str
    reference_image: str


class ArtStyle(BaseModel):
    """Art style configuration for image generation prompts."""

    prompt_prefix: str
    negative_prompt: str
    color_palette: list[str]


class ImageConfig(BaseModel):
    """Image generation provider and dimensions."""

    provider: str = "flux_kontext_pro"
    width: int = 1024
    height: int = 1024


class Layout(BaseModel):
    """Physical layout dimensions for print output."""

    trim_inches: list[float] = [8.5, 8.5]
    bleed_inches: float = 0.125
    safe_margin_inches: float = 0.25
    dpi: int = 300


class StyleGuide(BaseModel):
    """Complete style guide for a book series."""

    name: str
    version: int = 1
    art_style: ArtStyle
    image: ImageConfig = ImageConfig()
    characters: dict[str, CharacterDef]
    layout: Layout = Layout()

    def build_prompt_prefix(self) -> str:
        """Assemble full prompt prefix for image generation (STYL-04)."""
        char_descs = "; ".join(
            f"{c.name_en}: {c.description}" for c in self.characters.values()
        )
        return f"{self.art_style.prompt_prefix}. Characters: {char_descs}. --no {self.art_style.negative_prompt}"
