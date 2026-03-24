"""Tests for Claude story generation with streaming."""

from unittest.mock import MagicMock, patch

import pytest

from bookforge.story.generator import SYSTEM_PROMPT, generate_story


# --- Fixtures ---


def _make_mock_stream(final_text: str) -> MagicMock:
    """Create a mock that behaves like anthropic's stream context manager."""
    stream = MagicMock()
    stream.get_final_text.return_value = final_text
    stream.__enter__ = MagicMock(return_value=stream)
    stream.__exit__ = MagicMock(return_value=False)
    return stream


SAMPLE_GENERATED = """\
---
title: "The Magic Garden"
title_ko: "마법의 정원"
slug: magic-garden
trim_size: "8.5x8.5"
price: 4.99
ages: "4-8"
style_guide: korean-cute-watercolor
---

## Page 1

Once upon a time, there was a magical garden hidden behind the old library.

<!-- ko -->
옛날 옛적에, 오래된 도서관 뒤에 숨겨진 마법의 정원이 있었어요.
<!-- /ko -->

<!-- image: A hidden garden entrance with glowing flowers and a rustic wooden gate -->

## Page 2

Ho-rang the tiger cub discovered it one rainy afternoon.

<!-- ko -->
호랑이 새끼 호랑이가 비 오는 어느 오후에 그곳을 발견했어요.
<!-- /ko -->

<!-- image: A small tiger cub peeking through ivy-covered gate in gentle rain -->
"""


# --- Tests ---


class TestGenerateStory:
    """Tests for generate_story() function."""

    @patch("bookforge.story.generator.anthropic.Anthropic")
    def test_returns_yaml_frontmatter(self, mock_anthropic_cls: MagicMock) -> None:
        """Generated story contains YAML frontmatter delimiters."""
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.stream.return_value = _make_mock_stream(SAMPLE_GENERATED)

        result = generate_story("A story about a garden", "korean-cute-watercolor")
        assert "---" in result

    @patch("bookforge.story.generator.anthropic.Anthropic")
    def test_returns_page_headers(self, mock_anthropic_cls: MagicMock) -> None:
        """Generated story contains page headers."""
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.stream.return_value = _make_mock_stream(SAMPLE_GENERATED)

        result = generate_story("A story about a garden", "korean-cute-watercolor")
        assert "## Page 1" in result

    @patch("bookforge.story.generator.anthropic.Anthropic")
    def test_returns_korean_blocks(self, mock_anthropic_cls: MagicMock) -> None:
        """Generated story contains Korean comment blocks."""
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.stream.return_value = _make_mock_stream(SAMPLE_GENERATED)

        result = generate_story("A story about a garden", "korean-cute-watercolor")
        assert "<!-- ko -->" in result
        assert "<!-- /ko -->" in result

    @patch("bookforge.story.generator.anthropic.Anthropic")
    def test_returns_image_comments(self, mock_anthropic_cls: MagicMock) -> None:
        """Generated story contains image prompt comments."""
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.stream.return_value = _make_mock_stream(SAMPLE_GENERATED)

        result = generate_story("A story about a garden", "korean-cute-watercolor")
        assert "<!-- image:" in result

    @patch("bookforge.story.generator.anthropic.Anthropic")
    def test_uses_streaming(self, mock_anthropic_cls: MagicMock) -> None:
        """generate_story() uses streaming (.stream()), not .create()."""
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.stream.return_value = _make_mock_stream(SAMPLE_GENERATED)

        generate_story("A story about a garden", "korean-cute-watercolor")

        mock_client.messages.stream.assert_called_once()
        mock_client.messages.create.assert_not_called()

    @patch("bookforge.story.generator.anthropic.Anthropic")
    def test_passes_style_guide_in_message(self, mock_anthropic_cls: MagicMock) -> None:
        """Style guide name appears in the user message sent to Claude."""
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.stream.return_value = _make_mock_stream(SAMPLE_GENERATED)

        generate_story("A story", "my-custom-style")

        call_kwargs = mock_client.messages.stream.call_args
        messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
        user_msg = messages[0]["content"]
        assert "my-custom-style" in user_msg

    @patch("bookforge.story.generator.anthropic.Anthropic")
    def test_uses_model_from_env(self, mock_anthropic_cls: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
        """Model comes from BOOKFORGE_MODEL env var."""
        monkeypatch.setenv("BOOKFORGE_MODEL", "claude-test-model")
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.stream.return_value = _make_mock_stream(SAMPLE_GENERATED)

        generate_story("A story", "korean-cute-watercolor")

        call_kwargs = mock_client.messages.stream.call_args
        model = call_kwargs.kwargs.get("model") or call_kwargs[1].get("model")
        assert model == "claude-test-model"

    @patch("bookforge.story.generator.anthropic.Anthropic")
    def test_uses_default_model(self, mock_anthropic_cls: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
        """Default model is claude-sonnet-4-5 when BOOKFORGE_MODEL not set."""
        monkeypatch.delenv("BOOKFORGE_MODEL", raising=False)
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.stream.return_value = _make_mock_stream(SAMPLE_GENERATED)

        generate_story("A story", "korean-cute-watercolor")

        call_kwargs = mock_client.messages.stream.call_args
        model = call_kwargs.kwargs.get("model") or call_kwargs[1].get("model")
        assert model == "claude-sonnet-4-5"

    def test_system_prompt_has_format_instructions(self) -> None:
        """SYSTEM_PROMPT contains key format instructions."""
        assert "## Page" in SYSTEM_PROMPT
        assert "<!-- ko -->" in SYSTEM_PROMPT
        assert "<!-- image:" in SYSTEM_PROMPT
        assert "frontmatter" in SYSTEM_PROMPT.lower()
