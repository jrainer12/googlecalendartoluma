#!/usr/bin/env python3
"""
Tests for eventservice module.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta, timezone
import pytz
from icalendar import Calendar, Event
from app.services.eventservice import next_upcoming_events, fetch_events


class TestNextUpcomingEvents:
    """Tests for next_upcoming_events function."""
    
    def test_filters_past_events(self):
        """Test that past events are filtered out."""
        cal = Calendar()
        event = Event()
        event.add('summary', 'Past Event')
        past_time = datetime.now(pytz.UTC) - timedelta(days=1)
        event.add('dtstart', past_time)
        cal.add_component(event)
        
        future_event = Event()
        future_event.add('summary', 'Future Event')
        future_time = datetime.now(pytz.UTC) + timedelta(days=1)
        future_event.add('dtstart', future_time)
        cal.add_component(future_event)
        
        result = next_upcoming_events(cal, "America/New_York", limit=10)
        assert len(result) == 1
        assert result[0]["summary"] == "Future Event"
    
    def test_respects_limit(self):
        """Test that limit is respected."""
        cal = Calendar()
        for i in range(10):
            event = Event()
            event.add('summary', f'Event {i}')
            future_time = datetime.now(pytz.UTC) + timedelta(days=i+1)
            event.add('dtstart', future_time)
            cal.add_component(event)
        
        result = next_upcoming_events(cal, "America/New_York", limit=5)
        assert len(result) == 5
    
    def test_sorts_by_start_time(self):
        """Test that events are sorted by start time."""
        cal = Calendar()
        # Add events in reverse order
        for i in [3, 1, 2]:
            event = Event()
            event.add('summary', f'Event {i}')
            future_time = datetime.now(pytz.UTC) + timedelta(days=i)
            event.add('dtstart', future_time)
            cal.add_component(event)
        
        result = next_upcoming_events(cal, "America/New_York", limit=10)
        assert len(result) == 3
        assert result[0]["summary"] == "Event 1"
        assert result[1]["summary"] == "Event 2"
        assert result[2]["summary"] == "Event 3"
    
    def test_handles_missing_end_time(self):
        """Test that missing end time defaults correctly."""
        cal = Calendar()
        event = Event()
        event.add('summary', 'All Day Event')
        future_time = datetime.now(pytz.UTC) + timedelta(days=1)
        event.add('dtstart', future_time.date())  # All-day event
        cal.add_component(event)
        
        result = next_upcoming_events(cal, "America/New_York", limit=10)
        assert len(result) == 1
        assert result[0]["summary"] == "All Day Event"
        # End should be start + 1 day for all-day events
        assert result[0]["end_utc"] - result[0]["start_utc"] == timedelta(days=1)
    
    def test_handles_missing_dtstart(self):
        """Test that events without dtstart are skipped."""
        cal = Calendar()
        event = Event()
        event.add('summary', 'Event without start time')
        # No dtstart added
        cal.add_component(event)
        
        result = next_upcoming_events(cal, "America/New_York", limit=10)
        assert len(result) == 0
    
    def test_handles_event_with_dtend(self):
        """Test event with explicit dtend."""
        cal = Calendar()
        event = Event()
        event.add('summary', 'Event with end time')
        start_time = datetime.now(pytz.UTC) + timedelta(days=1)
        end_time = start_time + timedelta(hours=2)
        event.add('dtstart', start_time)
        event.add('dtend', end_time)
        cal.add_component(event)
        
        result = next_upcoming_events(cal, "America/New_York", limit=10)
        assert len(result) == 1
        assert result[0]["end_utc"] == end_time
    
    def test_handles_missing_summary(self):
        """Test that missing summary defaults to '(untitled)'."""
        cal = Calendar()
        event = Event()
        future_time = datetime.now(pytz.UTC) + timedelta(days=1)
        event.add('dtstart', future_time)
        cal.add_component(event)
        
        result = next_upcoming_events(cal, "America/New_York", limit=10)
        assert len(result) == 1
        assert result[0]["summary"] == "(untitled)"


class TestFetchEvents:
    """Tests for fetch_events function."""
    
    @pytest.mark.asyncio
    @patch('app.services.eventservice.load_ics')
    @patch('app.services.eventservice.embed_to_ics')
    @patch('app.services.eventservice.next_upcoming_events')
    @patch('app.services.eventservice.build_payload')
    @patch('aiofiles.open')
    @patch('os.makedirs')
    async def test_fetch_events_success(
        self, mock_makedirs, mock_aiofiles, mock_build_payload,
        mock_next_events, mock_embed_to_ics, mock_load_ics
    ):
        """Test successful event fetching."""
        # Setup mocks
        mock_embed_to_ics.return_value = ("https://example.com/calendar.ics", "America/New_York")
        mock_cal = MagicMock()
        mock_load_ics.return_value = mock_cal
        
        mock_events = [
            {
                "summary": "Test Event",
                "description": "Test Description",
                "location": "Test Location",
                "start_utc": datetime.now(timezone.utc) + timedelta(days=1),
                "end_utc": datetime.now(timezone.utc) + timedelta(days=1, hours=2)
            }
        ]
        mock_next_events.return_value = mock_events
        mock_build_payload.return_value = {"name": "Test Event"}
        
        mock_file = AsyncMock()
        mock_aiofiles.return_value.__aenter__.return_value = mock_file
        mock_aiofiles.return_value.__aexit__.return_value = None
        
        # Run function
        result = await fetch_events(
            "https://calendar.google.com/calendar/embed?src=test",
            "cal-test123",
            "America/New_York",
            5,
            "https://example.com/cover.jpg",
            "#FF0000",
            "geist-mono"
        )
        
        # Assertions
        assert result["success"] is True
        assert result["count"] == 1
        assert len(result["events"]) == 1
        assert result["timezone"] == "America/New_York"
        mock_embed_to_ics.assert_called_once()
        mock_load_ics.assert_called_once()
        mock_next_events.assert_called_once()
        mock_build_payload.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('app.services.eventservice.load_ics')
    @patch('app.services.eventservice.embed_to_ics')
    async def test_fetch_events_handles_error(
        self, mock_embed_to_ics, mock_load_ics
    ):
        """Test error handling in fetch_events."""
        mock_embed_to_ics.return_value = ("https://example.com/calendar.ics", "America/New_York")
        mock_load_ics.side_effect = Exception("Network error")
        
        result = await fetch_events(
            "https://calendar.google.com/calendar/embed?src=test",
            "cal-test123",
            "America/New_York",
            5,
            "https://example.com/cover.jpg",
            "#FF0000",
            "geist-mono"
        )
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    @patch('app.services.eventservice.load_ics')
    @patch('app.services.eventservice.embed_to_ics')
    @patch('app.services.eventservice.next_upcoming_events')
    @patch('app.services.eventservice.build_payload')
    @patch('aiofiles.open')
    @patch('os.makedirs')
    @patch('os.path.exists')
    async def test_fetch_events_with_existing_file(
        self, mock_exists, mock_makedirs, mock_aiofiles, mock_build_payload,
        mock_next_events, mock_embed_to_ics, mock_load_ics
    ):
        """Test fetch_events when output file already exists (uses indexed filename)."""
        mock_embed_to_ics.return_value = ("https://example.com/calendar.ics", "America/New_York")
        mock_cal = MagicMock()
        mock_load_ics.return_value = mock_cal
        
        mock_events = [
            {
                "summary": "Test Event",
                "description": "Test Description",
                "location": "Test Location",
                "start_utc": datetime.now(timezone.utc) + timedelta(days=1),
                "end_utc": datetime.now(timezone.utc) + timedelta(days=1, hours=2)
            }
        ]
        mock_next_events.return_value = mock_events
        mock_build_payload.return_value = {"name": "Test Event"}
        
        # First file exists, so it should use indexed filename
        mock_exists.side_effect = [True, False]  # test-event.json exists, test-event-1.json doesn't
        
        mock_file = AsyncMock()
        mock_aiofiles.return_value.__aenter__.return_value = mock_file
        mock_aiofiles.return_value.__aexit__.return_value = None
        
        result = await fetch_events(
            "https://calendar.google.com/calendar/embed?src=test",
            "cal-test123",
            "America/New_York",
            5,
            "https://example.com/cover.jpg",
            "#FF0000",
            "geist-mono"
        )
        
        assert result["success"] is True
        # Verify that aiofiles.open was called (file was written)
        mock_aiofiles.assert_called()

