#!/usr/bin/env python3
"""
Tests for build_geo_address function.
"""
import pytest
from main import build_geo_address


class TestBuildGeoAddress:
    """Tests for build_geo_address function."""
    
    def test_with_location(self):
        """Test building geo address with location."""
        result = build_geo_address("123 Main St, New York, NY")
        assert result is not None
        assert result["full_address"] == "123 Main St, New York, NY"
        assert result["address"] == "123 Main St, New York, NY"
        assert result["type"] == "text"
        assert result["description"] == ""
        assert result["city_state"] is None
        assert result["place_id"] is None
    
    def test_empty_location_returns_none(self):
        """Test that empty location returns None."""
        result = build_geo_address("")
        assert result is None
    
    def test_none_location_returns_none(self):
        """Test that None location returns None."""
        result = build_geo_address(None)
        assert result is None
    
    def test_strips_whitespace(self):
        """Test that whitespace is stripped."""
        result = build_geo_address("  123 Main St  ")
        assert result["full_address"] == "123 Main St"
        assert result["address"] == "123 Main St"

