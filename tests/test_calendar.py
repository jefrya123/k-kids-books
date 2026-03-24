"""Tests for calendar data model, YAML loading, and deadline computation."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest

from bookforge.calendar import CalendarEntry, compute_deadlines, get_upcoming, load_calendar


class TestCalendarEntry:
    """Tests for the CalendarEntry data model."""

    def test_creates_entry_with_defaults(self) -> None:
        entry = CalendarEntry(
            holiday_name="Chuseok",
            holiday_date=date(2026, 9, 25),
            slug="chuseok-story",
        )
        assert entry.holiday_name == "Chuseok"
        assert entry.holiday_date == date(2026, 9, 25)
        assert entry.slug == "chuseok-story"
        assert entry.status == "planned"

    def test_custom_status(self) -> None:
        entry = CalendarEntry(
            holiday_name="Seollal",
            holiday_date=date(2027, 2, 6),
            slug="seollal-story",
            status="in-progress",
        )
        assert entry.status == "in-progress"


class TestLoadCalendar:
    """Tests for load_calendar YAML loading."""

    def test_loads_entries_from_yaml(self, tmp_path: Path) -> None:
        yaml_content = """\
- holiday_name: "Christmas"
  holiday_date: 2026-12-25
  slug: christmas-story
  status: planned
- holiday_name: "Chuseok"
  holiday_date: 2026-09-25
  slug: chuseok-story
  status: in-progress
"""
        yaml_file = tmp_path / "content-calendar.yaml"
        yaml_file.write_text(yaml_content)

        entries = load_calendar(yaml_file)
        assert len(entries) == 2
        assert all(isinstance(e, CalendarEntry) for e in entries)

    def test_entries_sorted_by_date(self, tmp_path: Path) -> None:
        yaml_content = """\
- holiday_name: "Christmas"
  holiday_date: 2026-12-25
  slug: christmas-story
  status: planned
- holiday_name: "Chuseok"
  holiday_date: 2026-09-25
  slug: chuseok-story
  status: planned
- holiday_name: "Seollal"
  holiday_date: 2027-02-06
  slug: seollal-story
  status: planned
"""
        yaml_file = tmp_path / "content-calendar.yaml"
        yaml_file.write_text(yaml_content)

        entries = load_calendar(yaml_file)
        assert entries[0].holiday_name == "Chuseok"
        assert entries[1].holiday_name == "Christmas"
        assert entries[2].holiday_name == "Seollal"

    def test_missing_yaml_raises_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="content-calendar.yaml"):
            load_calendar(tmp_path / "content-calendar.yaml")


class TestComputeDeadlines:
    """Tests for backward deadline computation."""

    def test_release_date_21_days_before_holiday(self) -> None:
        entry = CalendarEntry(
            holiday_name="Chuseok",
            holiday_date=date(2026, 9, 25),
            slug="chuseok-story",
        )
        deadlines = compute_deadlines(entry)
        assert deadlines["release_date"] == date(2026, 9, 25) - timedelta(days=21)

    def test_marketing_start_35_days_before_holiday(self) -> None:
        entry = CalendarEntry(
            holiday_name="Chuseok",
            holiday_date=date(2026, 9, 25),
            slug="chuseok-story",
        )
        deadlines = compute_deadlines(entry)
        assert deadlines["marketing_start"] == date(2026, 9, 25) - timedelta(days=35)

    def test_illustration_start_42_days_before_holiday(self) -> None:
        entry = CalendarEntry(
            holiday_name="Chuseok",
            holiday_date=date(2026, 9, 25),
            slug="chuseok-story",
        )
        deadlines = compute_deadlines(entry)
        assert deadlines["illustration_start"] == date(2026, 9, 25) - timedelta(days=42)

    def test_writing_start_56_days_before_holiday(self) -> None:
        entry = CalendarEntry(
            holiday_name="Chuseok",
            holiday_date=date(2026, 9, 25),
            slug="chuseok-story",
        )
        deadlines = compute_deadlines(entry)
        assert deadlines["writing_start"] == date(2026, 9, 25) - timedelta(days=56)

    def test_all_deadlines_are_date_objects(self) -> None:
        entry = CalendarEntry(
            holiday_name="Christmas",
            holiday_date=date(2026, 12, 25),
            slug="christmas-story",
        )
        deadlines = compute_deadlines(entry)
        for key, value in deadlines.items():
            assert isinstance(value, date), f"{key} should be a date, got {type(value)}"


class TestGetUpcoming:
    """Tests for filtering upcoming entries."""

    def test_filters_past_entries(self) -> None:
        past = CalendarEntry(
            holiday_name="Past Holiday",
            holiday_date=date(2020, 1, 1),
            slug="past",
        )
        future = CalendarEntry(
            holiday_name="Future Holiday",
            holiday_date=date(2099, 12, 31),
            slug="future",
        )
        result = get_upcoming([past, future])
        assert len(result) == 1
        assert result[0].holiday_name == "Future Holiday"

    def test_includes_today(self) -> None:
        today_entry = CalendarEntry(
            holiday_name="Today Holiday",
            holiday_date=date.today(),
            slug="today",
        )
        result = get_upcoming([today_entry])
        assert len(result) == 1
