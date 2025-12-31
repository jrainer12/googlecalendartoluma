#!/usr/bin/env python3
"""
Tests for models module.
"""
import pytest
from app.models.models import (
    HealthResponse,
    GeoAddress,
    TicketType,
    EventPayload,
    EventResponse,
    EventsResponse,
    ErrorResponse,
    APIInfoResponse
)


class TestHealthResponse:
    """Tests for HealthResponse model."""
    
    def test_health_response_creation(self):
        """Test creating a health response."""
        response = HealthResponse(status="healthy")
        assert response.status == "healthy"
    
    def test_health_response_required_field(self):
        """Test that status is required."""
        with pytest.raises(Exception):  # Pydantic validation error
            HealthResponse()


class TestGeoAddress:
    """Tests for GeoAddress model."""
    
    def test_geo_address_creation(self):
        """Test creating a geo address."""
        address = GeoAddress(
            full_address="123 Main St",
            address="123 Main St"
        )
        assert address.full_address == "123 Main St"
        assert address.address == "123 Main St"
        assert address.type == "text"
        assert address.description == ""
    
    def test_geo_address_with_optional_fields(self):
        """Test geo address with optional fields."""
        address = GeoAddress(
            full_address="123 Main St, City, State",
            address="123 Main St",
            city="City",
            state="State",
            country="USA"
        )
        assert address.city == "City"


class TestTicketType:
    """Tests for TicketType model."""
    
    def test_ticket_type_defaults(self):
        """Test ticket type with defaults."""
        ticket = TicketType()
        assert ticket.type == "free"
        assert ticket.is_flexible is False
        assert ticket.require_approval is False
        assert ticket.is_hidden is False
        assert ticket.ethereum_token_requirements == []
    
    def test_ticket_type_with_values(self):
        """Test ticket type with custom values."""
        ticket = TicketType(
            type="paid",
            cents=1000,
            currency="USD"
        )
        assert ticket.type == "paid"
        assert ticket.cents == 1000
        assert ticket.currency == "USD"


class TestEventPayload:
    """Tests for EventPayload model."""
    
    def test_event_payload_creation(self):
        """Test creating an event payload."""
        payload = EventPayload(
            name="Test Event",
            start_at="2024-01-15T10:00:00.000Z",
            duration_interval="PT1H",
            cover_url="https://example.com/cover.jpg",
            timezone="America/New_York",
            calendar_api_id="cal-test123",
            tint_color="#FF0000",
            font_title="geist-mono",
            ticket_types=[]
        )
        assert payload.name == "Test Event"
        assert payload.start_at == "2024-01-15T10:00:00.000Z"
        assert payload.duration_interval == "PT1H"
        assert payload.visibility == "public"
        assert payload.location_type == "offline"
    
    def test_event_payload_with_geo_address(self):
        """Test event payload with geo address."""
        geo = GeoAddress(full_address="123 Main St", address="123 Main St")
        payload = EventPayload(
            name="Test Event",
            start_at="2024-01-15T10:00:00.000Z",
            duration_interval="PT1H",
            cover_url="https://example.com/cover.jpg",
            timezone="America/New_York",
            calendar_api_id="cal-test123",
            tint_color="#FF0000",
            font_title="geist-mono",
            ticket_types=[],
            geo_address_json=geo
        )
        assert payload.geo_address_json is not None
        assert payload.geo_address_json.full_address == "123 Main St"


class TestEventResponse:
    """Tests for EventResponse model."""
    
    def test_event_response_creation(self):
        """Test creating an event response."""
        event = EventPayload(
            name="Test Event",
            start_at="2024-01-15T10:00:00.000Z",
            duration_interval="PT1H",
            cover_url="https://example.com/cover.jpg",
            timezone="America/New_York",
            calendar_api_id="cal-test123",
            tint_color="#FF0000",
            font_title="geist-mono",
            ticket_types=[]
        )
        response = EventResponse(success=True, event=event)
        assert response.success is True
        assert response.event.name == "Test Event"


class TestEventsResponse:
    """Tests for EventsResponse model."""
    
    def test_events_response_creation(self):
        """Test creating an events response."""
        events = [
            EventPayload(
                name="Event 1",
                start_at="2024-01-15T10:00:00.000Z",
                duration_interval="PT1H",
                cover_url="https://example.com/cover.jpg",
                timezone="America/New_York",
                calendar_api_id="cal-test123",
                tint_color="#FF0000",
                font_title="geist-mono",
                ticket_types=[]
            )
        ]
        response = EventsResponse(
            success=True,
            count=1,
            events=events,
            timezone="America/New_York"
        )
        assert response.success is True
        assert response.count == 1
        assert len(response.events) == 1
        assert response.timezone == "America/New_York"


class TestErrorResponse:
    """Tests for ErrorResponse model."""
    
    def test_error_response_defaults(self):
        """Test error response with defaults."""
        response = ErrorResponse(error="Test error")
        assert response.success is False
        assert response.error == "Test error"


class TestAPIInfoResponse:
    """Tests for APIInfoResponse model."""
    
    def test_api_info_response_defaults(self):
        """Test API info response with defaults."""
        response = APIInfoResponse(endpoints={})
        assert response.service == "Google Calendar to Luma Sync API"
        assert response.version == "1.0.0"
        assert response.endpoints == {}
    
    def test_api_info_response_with_endpoints(self):
        """Test API info response with endpoints."""
        endpoints = {
            "health": "/health",
            "events": "/events"
        }
        response = APIInfoResponse(endpoints=endpoints)
        assert response.endpoints == endpoints

