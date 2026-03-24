"""Calendar loading, deadline computation, and table formatting for content-calendar.yaml."""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from pydantic import BaseModel
from ruamel.yaml import YAML


class CalendarEntry(BaseModel):
    """A single holiday release entry in the content calendar."""

    holiday_name: str
    holiday_date: date
    slug: str
    status: str = "planned"


def load_calendar(path: Path) -> list[CalendarEntry]:
    """Load content-calendar.yaml and return a sorted list of CalendarEntry.

    Args:
        path: Path to the content-calendar.yaml file.

    Returns:
        List of CalendarEntry sorted by holiday_date ascending.

    Raises:
        FileNotFoundError: If the YAML file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Calendar file not found: {path}")

    yaml = YAML()
    with open(path) as f:
        raw = yaml.load(f)

    # Convert ruamel CommentedSeq/CommentedMap to plain dicts via JSON round-trip
    entries_data = json.loads(json.dumps(raw, default=str))
    entries = [CalendarEntry(**item) for item in entries_data]
    return sorted(entries, key=lambda e: e.holiday_date)


def compute_deadlines(entry: CalendarEntry) -> dict[str, date]:
    """Compute backward-planned deadlines from a holiday date.

    Returns:
        Dict with keys: release_date (holiday - 21d), marketing_start (holiday - 35d),
        illustration_start (holiday - 42d), writing_start (holiday - 56d).
    """
    h = entry.holiday_date
    return {
        "release_date": h - timedelta(days=21),
        "marketing_start": h - timedelta(days=35),
        "illustration_start": h - timedelta(days=42),
        "writing_start": h - timedelta(days=56),
    }


def get_upcoming(entries: list[CalendarEntry]) -> list[CalendarEntry]:
    """Filter entries to only those with holiday_date >= today."""
    today = date.today()
    return [e for e in entries if e.holiday_date >= today]
