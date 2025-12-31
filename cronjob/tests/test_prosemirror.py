#!/usr/bin/env python3
"""
Tests for ProseMirror helper functions.
"""
import pytest
from main import make_pm_paragraph, to_prosemirror_doc


class TestMakePmParagraph:
    """Tests for make_pm_paragraph function."""
    
    def test_creates_paragraph(self):
        """Test creating a paragraph."""
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
        assert result is not None
        assert result["type"] == "doc"
        assert len(result["content"]) == 2
        assert result["content"][0]["content"][0]["text"] == "Event description"
        assert result["content"][1]["content"][0]["text"] == "Location: Event location"
    
    def test_with_description_only(self):
        """Test with description only."""
        result = to_prosemirror_doc("Event description", "")
        assert result is not None
        assert result["type"] == "doc"
        assert len(result["content"]) == 1
        assert result["content"][0]["content"][0]["text"] == "Event description"
    
    def test_with_location_only(self):
        """Test with location only."""
        result = to_prosemirror_doc("", "Event location")
        assert result is not None
        assert result["type"] == "doc"
        assert len(result["content"]) == 1
        assert result["content"][0]["content"][0]["text"] == "Location: Event location"
    
    def test_empty_returns_none(self):
        """Test that empty description and location returns None."""
        result = to_prosemirror_doc("", "")
        assert result is None
    
    def test_multiline_description(self):
        """Test multiline description."""
        result = to_prosemirror_doc("Line 1\nLine 2\n\nLine 3", "")
        assert result is not None
        assert len(result["content"]) == 4  # 3 lines + 1 empty paragraph
        assert result["content"][0]["content"][0]["text"] == "Line 1"
        assert result["content"][1]["content"][0]["text"] == "Line 2"
        assert result["content"][2] == {"type": "paragraph"}  # Empty paragraph
        assert result["content"][3]["content"][0]["text"] == "Line 3"

