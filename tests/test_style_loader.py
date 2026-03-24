"""Tests for style guide YAML loader (STYL-01 through STYL-05)."""

import pytest
from pathlib import Path
from pydantic import ValidationError

from bookforge.style.loader import load_style_guide


class TestLoadStyleGuide:
    """Test load_style_guide() loads YAML and validates via Pydantic."""

    def test_loads_valid_yaml_returns_style_guide(self, sample_style_yaml):
        """STYL-01: Style guide YAML loads into validated StyleGuide model."""
        sg = load_style_guide(sample_style_yaml)
        assert sg.name == "korean-cute-watercolor"

    def test_loads_characters_dict(self, sample_style_yaml):
        """STYL-02: Characters dict contains ho-rang and gom-i keys."""
        sg = load_style_guide(sample_style_yaml)
        assert "ho-rang" in sg.characters
        assert "gom-i" in sg.characters

    def test_character_def_fields(self, sample_style_yaml):
        """STYL-02: CharacterDef for ho-rang has all required fields."""
        sg = load_style_guide(sample_style_yaml)
        horang = sg.characters["ho-rang"]
        assert horang.name_en == "Ho-rang"
        assert horang.name_ko == "호랑"
        assert len(horang.description) > 0
        assert horang.reference_image == "characters/horang-ref.png"

    def test_image_provider_default(self, sample_style_yaml):
        """STYL-05: Image provider defaults to flux_kontext_pro."""
        sg = load_style_guide(sample_style_yaml)
        assert sg.image.provider == "flux_kontext_pro"

    def test_build_prompt_prefix_contains_style(self, sample_style_yaml):
        """STYL-04: build_prompt_prefix() contains prompt_prefix text."""
        sg = load_style_guide(sample_style_yaml)
        prefix = sg.build_prompt_prefix()
        assert sg.art_style.prompt_prefix in prefix

    def test_build_prompt_prefix_contains_character_desc(self, sample_style_yaml):
        """STYL-04: build_prompt_prefix() contains character description."""
        sg = load_style_guide(sample_style_yaml)
        prefix = sg.build_prompt_prefix()
        horang = sg.characters["ho-rang"]
        assert horang.description in prefix

    def test_build_prompt_prefix_contains_negative(self, sample_style_yaml):
        """STYL-04: build_prompt_prefix() contains negative prompt."""
        sg = load_style_guide(sample_style_yaml)
        prefix = sg.build_prompt_prefix()
        assert sg.art_style.negative_prompt in prefix

    def test_raises_on_missing_required_field(self, tmp_path):
        """load_style_guide raises error on YAML missing required field (art_style)."""
        bad_yaml = tmp_path / "bad.yaml"
        bad_yaml.write_text("name: test\ncharacters: {}\n")
        with pytest.raises(ValidationError):
            load_style_guide(bad_yaml)

    def test_raises_on_nonexistent_file(self, tmp_path):
        """load_style_guide raises error on non-existent file path."""
        missing = tmp_path / "does-not-exist.yaml"
        with pytest.raises(FileNotFoundError):
            load_style_guide(missing)
