"""Load and validate style guide YAML files using ruamel.yaml + Pydantic."""

import json
from pathlib import Path

from ruamel.yaml import YAML

from bookforge.style.schema import StyleGuide


def load_style_guide(path: Path) -> StyleGuide:
    """Load a style guide YAML file and return a validated StyleGuide model.

    Uses ruamel.yaml for comment-preserving YAML parsing, then converts
    the CommentedMap to a plain dict via JSON round-trip for Pydantic
    validation (Pitfall 2: never serialize Pydantic back through ruamel).

    Args:
        path: Path to the style guide YAML file.

    Returns:
        Validated StyleGuide instance.

    Raises:
        FileNotFoundError: If the YAML file does not exist.
        pydantic.ValidationError: If the YAML data fails schema validation.
    """
    if not path.exists():
        raise FileNotFoundError(f"Style guide not found: {path}")

    yaml = YAML()
    yaml.preserve_quotes = True
    with open(path) as f:
        data = yaml.load(f)

    # Convert ruamel CommentedMap to plain dict for Pydantic
    plain = json.loads(json.dumps(data, default=str))
    return StyleGuide(**plain)
