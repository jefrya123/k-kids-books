"""Claude API story generation with streaming."""

import anthropic

from bookforge.config import get_model

SYSTEM_PROMPT = """\
You are a children's book author writing bilingual English/Korean picture books.
Write a story in the exact bookforge story.md format:
- YAML frontmatter with title, title_ko, slug, trim_size, price, ages, style_guide fields
- Pages separated by ## Page N headers (starting at 1)
- English text bare (no markers)
- Korean text wrapped in <!-- ko --> / <!-- /ko --> blocks
- One <!-- image: [description] --> comment per page describing the illustration
Write {page_count} pages. Keep English simple (age {ages}). Korean should be grammatically natural.
"""


def generate_story(
    prompt: str,
    style_guide_name: str,
    page_count: int = 12,
    ages: str = "4-8",
) -> str:
    """Call Claude to generate a bilingual story draft with streaming.

    Args:
        prompt: One-line story idea from the user.
        style_guide_name: Name of the style guide to reference.
        page_count: Number of pages to generate.
        ages: Target age range for language simplicity.

    Returns:
        Raw story.md content as a string.
    """
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

    with client.messages.stream(
        model=get_model(),
        max_tokens=4096,
        system=SYSTEM_PROMPT.format(page_count=page_count, ages=ages),
        messages=[
            {
                "role": "user",
                "content": f"Write a children's book about: {prompt}\nStyle guide: {style_guide_name}",
            }
        ],
    ) as stream:
        return stream.get_final_text()
