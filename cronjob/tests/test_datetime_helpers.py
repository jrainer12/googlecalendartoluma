#!/usr/bin/env python3
"""
Tests for datetime helper functions.
"""
import pytest
from datetime import datetime, timezone, timedelta
from main import _to_dt, iso8601_z_with_ms, duration_from_range


class TestToDt:
    """Tests for _to_dt function."""
    
    def test_datetime_with_timezone(self):
        """Test datetime with timezone."""
        dt = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        result_dt, is_all_day = _to_dt(dt)
        assert result_dt == dt
        assert is_all_day is False
    
    def test_datetime_without_timezone(self):
        """Test datetime without timezone (should add UTC)."""
        dt = datetime(2024, 1, 15, 10, 0, 0)
        result_dt, is_all_day = _to_dt(dt)
        assert result_dt.tzinfo == timezone.utc
        assert is_all_day is False
    
    def test_date_all_day(self):
        """Test date object (all-day event)."""
        from datetime import date
        d = date(2024, 1, 15)
        result_dt, is_all_day = _to_dt(d)
        assert is_all_day is True
        assert result_dt.year == 2024
        assert result_dt.month == 1
        assert result_dt.day == 15
        assert result_dt.hour == 0
        assert result_dt.minute == 0


class TestIso8601ZWithMs:
    """Tests for iso8601_z_with_ms function."""
    
    def test_format_with_milliseconds(self):
        """Test formatting with milliseconds."""
        dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
        result = iso8601_z_with_ms(dt)
        assert result == "2024-01-15T10:30:45.000Z"
    
    def test_format_removes_timezone_offset(self):
        """Test that timezone offset is removed."""
        dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone(timedelta(hours=5)))
        result = iso8601_z_with_ms(dt.astimezone(timezone.utc))
        assert result.endswith("Z")
        assert "+" not in result
        assert "-" not in result or result.count("-") == 2  # Only date separators


class TestDurationFromRange:
    """Tests for duration_from_range function."""
    
    def test_one_hour_duration(self):
        """Test one hour duration."""
        start = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc)
        result = duration_from_range(start, end)
        assert result == "PT1H"
    
    def test_two_hours_thirty_minutes(self):
        """Test two hours and thirty minutes."""
        start = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 15, 12, 30, 0, tzinfo=timezone.utc)
        result = duration_from_range(start, end)
        assert result == "PT2H30M"
    
    def test_negative_duration_defaults_to_one_hour(self):
        """Test that negative duration defaults to one hour."""
        start = datetime(2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        result = duration_from_range(start, end)
        assert result == "PT1H"
    
    def test_minutes_and_seconds(self):
        """Test duration with minutes and seconds."""
        start = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 15, 10, 15, 30, tzinfo=timezone.utc)
        result = duration_from_range(start, end)
        assert result == "PT15M30S"

