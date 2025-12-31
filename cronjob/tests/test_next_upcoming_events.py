#!/usr/bin/env python3
"""
Tests for next_upcoming_events function.
"""
import pytest
from datetime import datetime, timezone, timedelta
from icalendar import Calendar, Event
from main import next_upcoming_events


class TestNextUpcomingEvents:
    """Tests for next_upcoming_events function."""
    
    def test_filters_past_events(self):
        """Test that past events are filtered out."""
        cal = Calendar()
        event = Event()
        past_time = datetime.now(timezone.utc) - timedelta(days=1)
        event.add('dtstart', past_time)
        event.add('summary', 'Past Event')
        cal.add_component(event)
        
        future_event = Event()
        future_time = datetime.now(timezone.utc) + timedelta(days=1)
        future_event.add('dtstart', future_time)
        future_event.add('summary', 'Future Event')
        cal.add_component(future_event)
        
        events = next_upcoming_events(cal, "UTC", limit=10)
        assert len(events) == 1
        assert events[0]["summary"] == "Future Event"
    
    def test_respects_limit(self):
        """Test that limit is respected."""
        cal = Calendar()
        base_time = datetime.now(timezone.utc) + timedelta(hours=1)
        for i in range(10):
            event = Event()
            event.add('dtstart', base_time + timedelta(hours=i))
            event.add('summary', f'Event {i}')
            cal.add_component(event)
        
        events = next_upcoming_events(cal, "UTC", limit=5)
        assert len(events) == 5
    
    def test_sorts_by_start_time(self):
        """Test that events are sorted by start time."""
        cal = Calendar()
        base_time = datetime.now(timezone.utc) + timedelta(hours=1)
        
        event3 = Event()
        event3.add('dtstart', base_time + timedelta(hours=3))
        event3.add('summary', 'Event 3')
        cal.add_component(event3)
        
        event1 = Event()
        event1.add('dtstart', base_time + timedelta(hours=1))
        event1.add('summary', 'Event 1')
        cal.add_component(event1)
        
        event2 = Event()
        event2.add('dtstart', base_time + timedelta(hours=2))
        event2.add('summary', 'Event 2')
        cal.add_component(event2)
        
        events = next_upcoming_events(cal, "UTC", limit=10)
        assert len(events) == 3
        assert events[0]["summary"] == "Event 1"
        assert events[1]["summary"] == "Event 2"
        assert events[2]["summary"] == "Event 3"
    
    def test_handles_missing_end_time(self):
        """Test handling missing end time (defaults to 1 hour later)."""
        cal = Calendar()
        start_time = datetime.now(timezone.utc) + timedelta(hours=1)
        event = Event()
        event.add('dtstart', start_time)
        event.add('summary', 'Event')
        cal.add_component(event)
        
        events = next_upcoming_events(cal, "UTC", limit=10)
        assert len(events) == 1
        assert events[0]["end_utc"] == start_time + timedelta(hours=1)
    
    def test_handles_missing_dtstart(self):
        """Test that events without dtstart are skipped."""
        cal = Calendar()
        event = Event()
        event.add('summary', 'Event without start')
        cal.add_component(event)
        
        events = next_upcoming_events(cal, "UTC", limit=10)
        assert len(events) == 0
    
    def test_handles_event_with_dtend(self):
        """Test event with explicit end time."""
        cal = Calendar()
        start_time = datetime.now(timezone.utc) + timedelta(hours=1)
        end_time = start_time + timedelta(hours=2)
        event = Event()
        event.add('dtstart', start_time)
        event.add('dtend', end_time)
        event.add('summary', 'Event')
        cal.add_component(event)
        
        events = next_upcoming_events(cal, "UTC", limit=10)
        assert len(events) == 1
        assert events[0]["end_utc"] == end_time
    
    def test_handles_missing_summary(self):
        """Test that missing summary defaults to '(untitled)'."""
        cal = Calendar()
        start_time = datetime.now(timezone.utc) + timedelta(hours=1)
        event = Event()
        event.add('dtstart', start_time)
        cal.add_component(event)
        
        events = next_upcoming_events(cal, "UTC", limit=10)
        assert len(events) == 1
        assert events[0]["summary"] == "(untitled)"

