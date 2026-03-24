"""Shared test fixtures for all test files."""

import pytest
from pathlib import Path


SAMPLE_STORY_MD = """\
---
title: "The Story of Dangun"
title_ko: "단군 이야기"
slug: dangun-story
trim_size: "8.5x8.5"
price: 4.99
ages: "4-8"
style_guide: korean-cute-watercolor
---

## Page 1

A long time ago, when the world was new, a great spirit lived in the sky.

<!-- ko -->
아주 먼 옛날, 세상이 새로웠을 때, 위대한 영혼이 하늘에 살았어요.
<!-- /ko -->

<!-- image: Misty mountain at dawn, soft watercolor style, clouds parting to reveal a glowing sky palace -->

## Page 2

Hwanin, the King of Heaven, looked down at the beautiful earth below.

<!-- ko -->
하늘의 왕 환인은 아래의 아름다운 땅을 내려다보았어요.
<!-- /ko -->

<!-- image: Kind elderly king in flowing white robes standing on golden clouds, gazing at green mountains below -->
"""


@pytest.fixture
def sample_story_md() -> str:
    """Raw markdown string for a 2-page sample story."""
    return SAMPLE_STORY_MD


@pytest.fixture
def sample_story_file(tmp_path: Path, sample_story_md: str) -> Path:
    """Write sample story to a temp file and return its path."""
    story_file = tmp_path / "story.md"
    story_file.write_text(sample_story_md)
    return story_file


@pytest.fixture
def sample_style_dict() -> dict:
    """Dict matching the StyleGuide schema with ho-rang and gom-i characters."""
    return {
        "name": "korean-cute-watercolor",
        "version": 1,
        "art_style": {
            "prompt_prefix": "Cute Korean watercolor children's book illustration, soft rounded characters, warm pastel tones",
            "negative_prompt": "photorealistic, dark, scary, violent, text, watermark",
            "color_palette": ["#FFB5C2", "#B5D8FF", "#FFE4B5", "#C2F0C2", "#E8D5F5"],
        },
        "image": {
            "provider": "flux_kontext_pro",
            "width": 1024,
            "height": 1024,
        },
        "characters": {
            "ho-rang": {
                "name_en": "Ho-rang",
                "name_ko": "호랑",
                "description": "A small, friendly tiger cub with round eyes, orange and black stripes, wearing a traditional Korean hanbok vest",
                "reference_image": "characters/horang-ref.png",
            },
            "gom-i": {
                "name_en": "Gom-i",
                "name_ko": "고미",
                "description": "A chubby, gentle bear cub with soft brown fur, round ears, and a warm smile, wearing a blue jeogori",
                "reference_image": "characters/gomi-ref.png",
            },
        },
        "layout": {
            "trim_inches": [8.5, 8.5],
            "bleed_inches": 0.125,
            "safe_margin_inches": 0.25,
            "dpi": 300,
        },
    }


@pytest.fixture
def sample_style_yaml(tmp_path: Path, sample_style_dict: dict) -> Path:
    """Write sample style dict as YAML to a temp file and return its path."""
    from ruamel.yaml import YAML

    yaml = YAML()
    style_file = tmp_path / "korean-cute-watercolor.yaml"
    with open(style_file, "w") as f:
        yaml.dump(sample_style_dict, f)
    return style_file


@pytest.fixture
def book_dir(tmp_path: Path) -> Path:
    """Create a temporary book directory structure."""
    book = tmp_path / "test-book"
    for subdir in ["images", "dist", "publish"]:
        (book / subdir).mkdir(parents=True)
    return book
