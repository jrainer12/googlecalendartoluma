#!/usr/bin/env python3
"""
Tests for load_ics function.
"""
import pytest
from unittest.mock import patch, MagicMock
from icalendar import Calendar
from main import load_ics


class TestLoadIcs:
    """Tests for load_ics function."""
    
    def test_loads_ics_successfully(self):
        """Test successfully loading ICS calendar."""
        mock_ics_content = b"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test//EN
BEGIN:VEVENT
SUMMARY:Test Event
DTSTART:20240115T100000Z
END:VEVENT
END:VCALENDAR"""
        
        with patch('main.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.content = mock_ics_content
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            result = load_ics("https://example.com/calendar.ics")
            assert result is not None
            assert isinstance(result, Calendar)
            mock_response.raise_for_status.assert_called_once()
    
    def test_raises_error_on_http_failure(self):
        """Test that error is raised on HTTP failure."""
        import requests
        
        with patch('main.requests.get') as mock_get:
            mock_get.side_effect = requests.RequestException("Connection error")
            
            with pytest.raises(requests.RequestException):
                load_ics("https://example.com/calendar.ics")
    
    def test_raises_error_on_http_status_error(self):
        """Test that error is raised on HTTP status error."""
        import requests
        
        with patch('main.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
            mock_get.return_value = mock_response
            
            with pytest.raises(requests.HTTPError):
                load_ics("https://example.com/calendar.ics")

