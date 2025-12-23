#!/usr/bin/env python3
"""
Tests for payloadbuilder module.
"""
import pytest
from datetime import datetime, timezone, timedelta
from app.services.payloadbuilder import (
    _to_dt,
    iso8601_z_with_ms,
    duration_from_range,
    make_pm_paragraph,
    to_prosemirror_doc,
    build_geo_address,
    build_payload,
    _slugify_filename
)


class TestToDt:
    """Tests for _to_dt function."""
    
    def test_datetime_with_timezone(self):
        """Test datetime with timezone."""
        dt = datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc)
        result, is_all_day = _to_dt(dt)
        assert result == dt
        assert is_all_day is False
    
    def test_datetime_without_timezone(self):
        """Test datetime without timezone (should add UTC)."""
        dt = datetime(2024, 1, 15, 10, 30)
        result, is_all_day = _to_dt(dt)
        assert result.tzinfo == timezone.utc
        assert is_all_day is False
    
    def test_date_all_day(self):
        """Test date object (all-day event)."""
        from datetime import date
        d = date(2024, 1, 15)
        result, is_all_day = _to_dt(d)
        assert result == datetime(2024, 1, 15, 0, 0, tzinfo=timezone.utc)
        assert is_all_day is True


class TestIso8601ZWithMs:
    """Tests for iso8601_z_with_ms function."""
    
    def test_format_with_milliseconds(self):
        """Test ISO8601 format with milliseconds and Z suffix."""
        dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
        result = iso8601_z_with_ms(dt)
        assert result == "2024-01-15T10:30:45.000Z"
    
    def test_format_removes_timezone_offset(self):
        """Test that timezone offset is removed."""
        dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone(timedelta(hours=5)))
        result = iso8601_z_with_ms(dt)
        # Should convert to UTC
        assert result.endswith(".000Z")


class TestDurationFromRange:
    """Tests for duration_from_range function."""
    
    def test_one_hour_duration(self):
        """Test one hour duration."""
        start = datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc)
        result = duration_from_range(start, end)
        assert result == "PT1H"
    
    def test_two_hours_thirty_minutes(self):
        """Test 2h 30m duration."""
        start = datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 15, 12, 30, tzinfo=timezone.utc)
        result = duration_from_range(start, end)
        assert result == "PT2H30M"
    
    def test_negative_duration_defaults_to_one_hour(self):
        """Test that negative duration defaults to 1 hour."""
        start = datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc)  # Before start
        result = duration_from_range(start, end)
        assert result == "PT1H"
    
    def test_minutes_and_seconds(self):
        """Test duration with minutes and seconds."""
        start = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 15, 10, 15, 30, tzinfo=timezone.utc)
        result = duration_from_range(start, end)
        assert result == "PT15M30S"


class TestMakePmParagraph:
    """Tests for make_pm_paragraph function."""
    
    def test_creates_paragraph(self):
        """Test paragraph creation."""
        result = make_pm_paragraph("Test text")
        assert result == {
            "type": "paragraph",
            "content": [{"type": "text", "text": "Test text"}]
        }


class TestToProsemirrorDoc:
    """Tests for to_prosemirror_doc function."""
    
    def test_with_description_and_location(self):
        """Test with both description and location."""
        result = to_prosemirror_doc("Event description", "Event location")
        assert result["type"] == "doc"
        assert len(result["content"]) == 2
        assert result["content"][0]["content"][0]["text"] == "Event description"
        assert result["content"][1]["content"][0]["text"] == "Location: Event location"
    
    def test_with_description_only(self):
        """Test with description only."""
        result = to_prosemirror_doc("Event description", "")
        assert result["type"] == "doc"
        assert len(result["content"]) == 1
    
    def test_with_location_only(self):
        """Test with location only."""
        result = to_prosemirror_doc("", "Event location")
        assert result["type"] == "doc"
        assert len(result["content"]) == 1
        assert "Location: Event location" in result["content"][0]["content"][0]["text"]
    
    def test_empty_returns_none(self):
        """Test that empty description and location returns None."""
        result = to_prosemirror_doc("", "")
        assert result is None
    
    def test_multiline_description(self):
        """Test multiline description."""
        desc = "Line 1\nLine 2\n\nLine 3"
        result = to_prosemirror_doc(desc, "")
        assert len(result["content"]) == 4  # 3 lines + 1 empty paragraph


class TestBuildGeoAddress:
    """Tests for build_geo_address function."""
    
    def test_with_location(self):
        """Test with location text."""
        result = build_geo_address("123 Main St, City, State")
        assert result["full_address"] == "123 Main St, City, State"
        assert result["address"] == "123 Main St, City, State"
        assert result["type"] == "text"
    
    def test_empty_location_returns_none(self):
        """Test that empty location returns None."""
        result = build_geo_address("")
        assert result is None
    
    def test_none_location_returns_none(self):
        """Test that None location returns None."""
        result = build_geo_address(None)
        assert result is None


class TestBuildPayload:
    """Tests for build_payload function."""
    
    def test_builds_complete_payload(self):
        """Test building a complete payload."""
        ev = {
            "summary": "Test Event",
            "description": "Event description",
            "location": "Test Location",
            "start_utc": datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
            "end_utc": datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc)
        }
        result = build_payload(
            ev,
            "America/New_York",
            "cal-test123",
            "https://example.com/cover.jpg",
            "#FF0000",
            "geist-mono"
        )
        assert result["name"] == "Test Event"
        assert result["start_at"] == "2024-01-15T10:00:00.000Z"
        assert result["duration_interval"] == "PT1H"
        assert result["timezone"] == "America/New_York"
        assert result["calendar_api_id"] == "cal-test123"
        assert result["cover_url"] == "https://example.com/cover.jpg"
        assert result["tint_color"] == "#FF0000"
        assert result["font_title"] == "geist-mono"
        assert result["description_mirror"] is not None
        assert result["geo_address_json"] is not None


class TestSlugifyFilename:
    """Tests for _slugify_filename function."""
    
    def test_simple_name(self):
        """Test simple event name."""
        result = _slugify_filename("Test Event")
        assert result == "test-event"
    
    def test_with_special_characters(self):
        """Test with special characters."""
        result = _slugify_filename("Test Event @ 2024!")
        assert result == "test-event-2024"
    
    def test_multiple_spaces(self):
        """Test multiple spaces become single dash."""
        result = _slugify_filename("Test   Event")
        assert result == "test-event"
    
    def test_empty_name_defaults_to_event(self):
        """Test that empty name defaults to 'event'."""
        result = _slugify_filename("")
        assert result == "event"
    
    def test_only_special_characters(self):
        """Test name with only special characters."""
        result = _slugify_filename("!!!")
        assert result == "event"

