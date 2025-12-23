#!/usr/bin/env python3
"""
Tests for build_payload function.
"""
import pytest
from datetime import datetime, timezone, timedelta
from main import build_payload


class TestBuildPayload:
    """Tests for build_payload function."""
    
    def test_builds_complete_payload(self):
        """Test building a complete payload."""
        ev = {
            "summary": "Test Event",
            "description": "Event description",
            "location": "123 Main St",
            "start_utc": datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            "end_utc": datetime(2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc)
        }
        tzname = "America/New_York"
        calendar_api_id = "cal-test123"
        
        payload = build_payload(ev, tzname, calendar_api_id)
        
        assert payload["name"] == "Test Event"
        assert payload["start_at"] == "2024-01-15T10:00:00.000Z"
        assert payload["duration_interval"] == "PT1H"
        assert payload["timezone"] == tzname
        assert payload["calendar_api_id"] == calendar_api_id
        assert payload["description_mirror"] is not None
        assert payload["geo_address_json"] is not None
        assert payload["geo_address_json"]["full_address"] == "123 Main St"
        assert payload["ticket_types"] is not None
        assert len(payload["ticket_types"]) == 1
        assert payload["ticket_types"][0]["type"] == "free"
    
    def test_builds_payload_without_location(self):
        """Test building payload without location."""
        ev = {
            "summary": "Test Event",
            "description": "Event description",
            "location": "",
            "start_utc": datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            "end_utc": datetime(2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc)
        }
        tzname = "UTC"
        calendar_api_id = "cal-test123"
        
        payload = build_payload(ev, tzname, calendar_api_id)
        
        assert payload["geo_address_json"] is None
        assert payload["description_mirror"] is not None
    
    def test_builds_payload_without_description(self):
        """Test building payload without description."""
        ev = {
            "summary": "Test Event",
            "description": "",
            "location": "123 Main St",
            "start_utc": datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            "end_utc": datetime(2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc)
        }
        tzname = "UTC"
        calendar_api_id = "cal-test123"
        
        payload = build_payload(ev, tzname, calendar_api_id)
        
        # Should still have description_mirror with location
        assert payload["description_mirror"] is not None
        assert payload["geo_address_json"] is not None

