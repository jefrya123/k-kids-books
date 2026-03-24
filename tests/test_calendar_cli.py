"""Tests for the CLI calendar command."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from bookforge.cli import app

runner = CliRunner()


@pytest.fixture
def calendar_yaml(tmp_path: Path, monkeypatch) -> Path:
    """Create a content-calendar.yaml with future and past entries."""
    yaml_content = """\
- holiday_name: "Ancient Holiday"
  holiday_date: 2020-01-01
  slug: ancient-story
  status: done
- holiday_name: "Future Chuseok"
  holiday_date: 2099-09-25
  slug: chuseok-story
  status: planned
- holiday_name: "Future Christmas"
  holiday_date: 2099-12-25
  slug: christmas-story
  status: in-progress
"""
    yaml_file = tmp_path / "content-calendar.yaml"
    yaml_file.write_text(yaml_content)
    monkeypatch.chdir(tmp_path)
    return yaml_file


class TestCalendarCommand:
    """Tests for the calendar CLI command."""

    def test_shows_upcoming_entries(self, calendar_yaml: Path) -> None:
        result = runner.invoke(app, ["calendar"])
        assert result.exit_code == 0, result.output
        assert "Future Chuseok" in result.output
        assert "Future Christmas" in result.output

    def test_hides_past_entries_by_default(self, calendar_yaml: Path) -> None:
        result = runner.invoke(app, ["calendar"])
        assert result.exit_code == 0, result.output
        assert "Ancient Holiday" not in result.output

    def test_all_flag_shows_past_entries(self, calendar_yaml: Path) -> None:
        result = runner.invoke(app, ["calendar", "--all"])
        assert result.exit_code == 0, result.output
        assert "Ancient Holiday" in result.output
        assert "Future Chuseok" in result.output

    def test_shows_dates_in_table(self, calendar_yaml: Path) -> None:
        result = runner.invoke(app, ["calendar", "--all"])
        assert result.exit_code == 0, result.output
        # Check that holiday date appears
        assert "2099-09-25" in result.output

    def test_shows_computed_deadlines(self, calendar_yaml: Path) -> None:
        result = runner.invoke(app, ["calendar", "--all"])
        assert result.exit_code == 0, result.output
        # Release date = 2099-09-25 - 21 days = 2099-09-04
        assert "2099-09-04" in result.output

    def test_missing_yaml_shows_helpful_error(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["calendar"])
        assert result.exit_code == 1
        assert "content-calendar.yaml" in result.output
        # Should show example format
        assert "holiday_name" in result.output

    def test_shows_slug_column(self, calendar_yaml: Path) -> None:
        result = runner.invoke(app, ["calendar"])
        assert result.exit_code == 0, result.output
        assert "chuseok-story" in result.output

    def test_shows_status_column(self, calendar_yaml: Path) -> None:
        result = runner.invoke(app, ["calendar"])
        assert result.exit_code == 0, result.output
        assert "planned" in result.output
