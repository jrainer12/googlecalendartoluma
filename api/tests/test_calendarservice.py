#!/usr/bin/env python3
"""
Tests for calendarservice module.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from urllib.parse import urlparse, parse_qs
from app.services.calendarservice import embed_to_ics, load_ics


class TestEmbedToIcs:
    """Tests for embed_to_ics function."""
    
    def test_converts_embed_url_to_ics(self):
        """Test converting embed URL to ICS URL."""
        embed_url = "https://calendar.google.com/calendar/embed?src=test%40group.calendar.google.com&ctz=America%2FNew_York"
        ics_url, tz = embed_to_ics(embed_url)
        assert "calendar.google.com/calendar/ical" in ics_url
        assert "test@group.calendar.google.com" in ics_url
        assert "public/full.ics" in ics_url
        assert tz == "America/New_York"
    
    def test_uses_default_timezone_when_not_specified(self):
        """Test that default timezone is used when not in URL."""
        embed_url = "https://calendar.google.com/calendar/embed?src=test%40group.calendar.google.com"
        ics_url, tz = embed_to_ics(embed_url, default_timezone="America/Los_Angeles")
        assert tz == "America/Los_Angeles"
    
    def test_raises_error_when_no_src(self):
        """Test that ValueError is raised when no src parameter."""
        embed_url = "https://calendar.google.com/calendar/embed?ctz=America%2FNew_York"
        with pytest.raises(ValueError, match="No 'src' in embed URL"):
            embed_to_ics(embed_url)
    
    def test_url_decodes_calendar_id(self):
        """Test that calendar ID is URL decoded."""
        embed_url = "https://calendar.google.com/calendar/embed?src=test%40example.com"
        ics_url, _ = embed_to_ics(embed_url)
        assert "test@example.com" in ics_url


class TestLoadIcs:
    """Tests for load_ics function."""
    
    @pytest.mark.asyncio
    async def test_loads_ics_successfully(self):
        """Test successfully loading ICS calendar."""
        mock_ics_content = b"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test//EN
BEGIN:VEVENT
SUMMARY:Test Event
DTSTART:20240115T100000Z
END:VEVENT
END:VCALENDAR"""
        
        with patch('app.services.calendarservice.httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.content = mock_ics_content
            mock_response.raise_for_status = MagicMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_client_instance
            
            result = await load_ics("https://example.com/calendar.ics")
            assert result is not None
            mock_response.raise_for_status.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_raises_error_on_http_failure(self):
        """Test that HTTPError is raised on HTTP failure."""
        with patch('app.services.calendarservice.httpx.AsyncClient') as mock_client:
            import httpx
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get.side_effect = httpx.HTTPError("Connection failed")
            mock_client.return_value = mock_client_instance
            
            with pytest.raises(httpx.HTTPError):
                await load_ics("https://example.com/calendar.ics")

