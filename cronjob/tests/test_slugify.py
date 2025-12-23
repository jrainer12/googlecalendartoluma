#!/usr/bin/env python3
"""
Tests for _slugify_filename function.
"""
import pytest
from main import _slugify_filename


class TestSlugifyFilename:
    """Tests for _slugify_filename function."""
    
    def test_simple_name(self):
        """Test simple event name."""
        assert _slugify_filename("Club Meeting") == "club-meeting"
    
    def test_with_special_characters(self):
        """Test name with special characters."""
        assert _slugify_filename("Event@#$%Name!") == "eventname"
    
    def test_multiple_spaces(self):
        """Test name with multiple spaces."""
        assert _slugify_filename("Event   Name") == "event-name"
    
    def test_empty_name_defaults_to_event(self):
        """Test that empty name defaults to 'event'."""
        assert _slugify_filename("") == "event"
        assert _slugify_filename("   ") == "event"
    
    def test_only_special_characters(self):
        """Test name with only special characters."""
        assert _slugify_filename("@#$%") == "event"
    
    def test_with_underscores(self):
        """Test name with underscores."""
        assert _slugify_filename("event_name") == "event-name"
    
    def test_with_dashes(self):
        """Test name with dashes."""
        assert _slugify_filename("event-name") == "event-name"
    
    def test_mixed_case(self):
        """Test mixed case name."""
        assert _slugify_filename("EventName") == "eventname"
    
    def test_leading_trailing_dashes(self):
        """Test that leading/trailing dashes are removed."""
        assert _slugify_filename("-event-name-") == "event-name"
    
    def test_multiple_consecutive_dashes(self):
        """Test that multiple consecutive dashes are collapsed."""
        assert _slugify_filename("event---name") == "event-name"

