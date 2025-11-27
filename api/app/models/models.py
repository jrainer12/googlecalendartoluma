#!/usr/bin/env python3
"""
Pydantic models for API request/response validation.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Health status of the API")


class GeoAddress(BaseModel):
    """Geographic address model for event locations."""
    description: str = ""
    full_address: str
    city_state: Optional[str] = None
    type: str = "text"
    address: str
    place_id: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    region: Optional[str] = None


class TicketType(BaseModel):
    """Ticket type model for events."""
    type: str = "free"
    ethereum_token_requirements: List[dict] = []
    cents: Optional[int] = None
    is_flexible: bool = False
    min_cents: Optional[int] = None
    require_approval: bool = False
    currency: Optional[str] = None
    is_hidden: bool = False


class EventPayload(BaseModel):
    """Luma-compatible event payload model."""
    name: str = Field(..., description="Event name")
    start_at: str = Field(..., description="Event start time in ISO8601 format")
    duration_interval: str = Field(..., description="Event duration in ISO8601 duration format")
    zoom_meeting_url: Optional[str] = None
    zoom_meeting_id: Optional[str] = None
    zoom_meeting_password: Optional[str] = None
    description_mirror: Optional[dict] = None
    geo_address_visibility: str = "public"
    cover_url: str
    zoom_session_type: Optional[str] = None
    zoom_creation_method: Optional[str] = None
    location_type: str = "offline"
    geo_address_json: Optional[GeoAddress] = None
    coordinate: Optional[dict] = None
    timezone: str
    calendar_api_id: str
    calendar_to_submit_to_api_id: Optional[str] = None
    supports_members_only: bool = False
    max_capacity: Optional[int] = None
    waitlist_enabled: bool = False
    visibility: str = "public"
    theme_meta: dict = {"theme": "legacy"}
    tint_color: str
    font_title: str
    ticket_types: List[TicketType]


class EventResponse(BaseModel):
    """Response model for a single event."""
    success: bool = Field(..., description="Whether the operation was successful")
    event: EventPayload = Field(..., description="The event payload")


class EventsResponse(BaseModel):
    """Response model for multiple events."""
    success: bool = Field(..., description="Whether the operation was successful")
    count: int = Field(..., description="Number of events returned")
    events: List[EventPayload] = Field(..., description="List of event payloads")
    timezone: str = Field(..., description="Timezone used for event processing")


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: str = Field(..., description="Error message")


class APIInfoResponse(BaseModel):
    """API information response model."""
    service: str = "Google Calendar to Luma Sync API"
    version: str = "1.0.0"
    endpoints: dict = Field(..., description="Available API endpoints")

