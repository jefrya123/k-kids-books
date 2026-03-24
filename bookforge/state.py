"""Book state management with atomic write pattern."""

import json
import os
from pathlib import Path


def load_state(book_dir: Path) -> dict:
    """Load state.json from a book directory. Returns empty dict if not found."""
    state_path = book_dir / "state.json"
    if not state_path.exists():
        return {}
    return json.loads(state_path.read_text())


def save_state(book_dir: Path, state: dict) -> None:
    """Atomic write: write to .tmp then os.replace() to avoid corruption."""
    state_path = book_dir / "state.json"
    tmp_path = state_path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(state, indent=2, default=str))
    os.replace(tmp_path, state_path)
