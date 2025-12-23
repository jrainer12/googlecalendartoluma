#!/usr/bin/env python3
"""
Tests for embed_to_ics function.
"""
import pytest
from main import embed_to_ics, TIMEZONE_NAME


class TestEmbedToIcs:
    """Tests for embed_to_ics function."""
    
    def test_converts_embed_url_to_ics(self):
        """Test converting embed URL to ICS URL."""
        embed_url = "https://calendar.google.com/calendar/embed?src=test%40group.calendar.google.com&ctz=America%2FNew_York"
        ics_url, tz = embed_to_ics(embed_url)
        assert ics_url == "https://calendar.google.com/calendar/ical/test@group.calendar.google.com/public/full.ics"
        assert tz == "America/New_York"
    
    def test_uses_default_timezone_when_not_specified(self):
        """Test that default timezone is used when not in URL."""
        embed_url = "https://calendar.google.com/calendar/embed?src=test%40group.calendar.google.com"
        ics_url, tz = embed_to_ics(embed_url)
        assert ics_url == "https://calendar.google.com/calendar/ical/test@group.calendar.google.com/public/full.ics"
        assert tz == TIMEZONE_NAME
    
    def test_raises_error_when_no_src(self):
        """Test that error is raised when no src parameter."""
        embed_url = "https://calendar.google.com/calendar/embed?ctz=America%2FNew_York"
        with pytest.raises(ValueError, match="No 'src' in embed URL"):
            embed_to_ics(embed_url)
    
    def test_url_decodes_calendar_id(self):
        """Test that calendar ID is URL decoded."""
        embed_url = "https://calendar.google.com/calendar/embed?src=test%2Bgroup%40example.com&ctz=UTC"
        ics_url, tz = embed_to_ics(embed_url)
        assert "test+group@example.com" in ics_url

