#!/usr/bin/env python3
# API server for Google Calendar to Luma sync
"""
FastAPI application entrypoint.
This module contains only the HTTP routes and application setup.
Business logic is in app/services/, models are in app/models/,
and utilities are in app/util/.
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, Path, APIRouter, Request
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi

from app.util.config import config, get_base_route_http
from app.util.app_config import get_base_route_sync, setup_middleware
from app.util.app_setup import setup_app
from app.models.models import (
    HealthResponse,
    EventPayload,
    EventsResponse,
    EventResponse,
    APIInfoResponse
)
from app.services.eventservice import fetch_events

# Configure logging - will be updated after config loads
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create API router - will be mounted with base route prefix after config loads
api_router = APIRouter()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup - setup application
    await setup_app(app, api_router)
    
    yield  # Application is running
    
    # Shutdown (if needed in the future)
    logger.info("Application shutting down")


# Get base route synchronously (before config loads)
# This will be overridden with actual config value in lifespan handler if different
_base_route_sync = get_base_route_sync()

# Create main FastAPI app with lifespan handler
# Don't use root_path - the ingress forwards the full path, router handles the prefix
# Docs will be added to the router so they're under the base route
app = FastAPI(
    title="Google Calendar to Luma Sync API",
    description="REST API that exposes Google Calendar events as Luma-compatible JSON payloads",
    version="1.0.0",
    docs_url=None,  # Disabled - we add docs to router
    redoc_url=None,  # Disabled - we add docs to router
    lifespan=lifespan
)

# Setup middleware (CORS, health check logging suppression)
setup_middleware(app)


# Health check endpoint function - will be registered at both root and router level
async def health_check():
    """Health check endpoint - accessible at root level for Kubernetes probes.
    
    This endpoint is always available, even before configuration loads.
    It does not depend on any application state or configuration.
    """
    logger.debug("Health check endpoint called")
    return HealthResponse(status="healthy")


# Register health endpoint at root level (for Kubernetes probes)
# This must be available immediately, even before config loads
@app.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check if the API is running and healthy",
    tags=["Health"],
    include_in_schema=True
)
async def health():
    """Health check endpoint - accessible at root level for Kubernetes probes"""
    return await health_check()


# Also register on router so it's available at base_route/health
@api_router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check if the API is running and healthy",
    tags=["Health"],
    include_in_schema=True
)
async def health_router():
    """Health check endpoint - also available at base route"""
    return await health_check()


@api_router.get(
    "/events",
    response_model=EventsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all upcoming events",
    description="Fetch all upcoming events from Google Calendar and return them as Luma-compatible JSON payloads",
    tags=["Events"]
)
async def get_events():
    """Get all upcoming events from Google Calendar"""
    # Access config like Quart: config['events']['cover_url'] or config.get('events', {}).get('cover_url')
    calendar_config = config.get('calendar', {})
    events_config = config.get('events', {})
    
    result = await fetch_events(
        gcal_embed_url=calendar_config.get('gcal_embed_url', 'https://calendar.google.com/calendar/embed?src=tnti8oguf84qd354budk86vdpk%40group.calendar.google.com&ctz=America%2FNew_York'),
        luma_calendar_api_id=calendar_config.get('luma_calendar_api_id', 'cal-iPlAn4RA1wD1lDh'),
        timezone_name=events_config.get('timezone_name', 'America/New_York'),
        limit=events_config.get('limit', 5),
        cover_url=events_config.get('cover_url', 'https://images.lumacdn.com/gallery-images/vn/e95edc2d-7ad2-45a0-ba4c-393e17cb8f60'),
        tint_color=events_config.get('tint_color', '#708967'),
        font_title=events_config.get('font_title', 'geist-mono'),
        out_dir=events_config.get('out_dir', 'luma_payloads')
    )
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Failed to fetch events")
        )
    return EventsResponse(**result)


@api_router.get(
    "/events/{event_id}",
    response_model=EventResponse,
    status_code=status.HTTP_200_OK,
    summary="Get specific event by ID",
    description="Get a specific event by its ID (1-indexed)",
    tags=["Events"]
)
async def get_event(event_id: int = Path(..., ge=1, description="Event ID (1-indexed)")):
    """Get a specific event by ID"""
    # Access config like Quart: config['events']['cover_url'] or config.get('events', {}).get('cover_url')
    calendar_config = config.get('calendar', {})
    events_config = config.get('events', {})
    
    result = await fetch_events(
        gcal_embed_url=calendar_config.get('gcal_embed_url', 'https://calendar.google.com/calendar/embed?src=tnti8oguf84qd354budk86vdpk%40group.calendar.google.com&ctz=America%2FNew_York'),
        luma_calendar_api_id=calendar_config.get('luma_calendar_api_id', 'cal-iPlAn4RA1wD1lDh'),
        timezone_name=events_config.get('timezone_name', 'America/New_York'),
        limit=events_config.get('limit', 5),
        cover_url=events_config.get('cover_url', 'https://images.lumacdn.com/gallery-images/vn/e95edc2d-7ad2-45a0-ba4c-393e17cb8f60'),
        tint_color=events_config.get('tint_color', '#708967'),
        font_title=events_config.get('font_title', 'geist-mono'),
        out_dir=events_config.get('out_dir', 'luma_payloads')
    )
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Failed to fetch events")
        )

    if event_id < 1 or event_id > result["count"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event ID {event_id} not found. Available IDs: 1-{result['count']}"
        )

    return EventResponse(
        success=True,
        event=result["events"][event_id - 1]
    )


@api_router.get(
    "/",
    response_model=APIInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="API information",
    description="Get information about the API and available endpoints",
    tags=["Info"]
)
async def root():
    """Root endpoint with API information"""
    base_route = get_base_route_http()
    return APIInfoResponse(
        service="Google Calendar to Luma Sync API",
        version="1.0.0",
        endpoints={
            f"{base_route}/health": "Health check",
            f"{base_route}/events": "Get all upcoming events",
            f"{base_route}/events/{{id}}": "Get specific event by ID (1-indexed)",
            f"{base_route}/docs": "Swagger UI documentation",
            f"{base_route}/redoc": "ReDoc documentation"
        }
    )


# Add docs endpoints to router so they're accessible under base route
@api_router.get("/docs", include_in_schema=False)
async def swagger_ui(request: Request):
    """Swagger UI documentation"""
    base_route = get_base_route_http()
    return get_swagger_ui_html(
        openapi_url=f"{base_route}/openapi.json",
        title=app.title + " - Swagger UI"
    )


@api_router.get("/redoc", include_in_schema=False)
async def redoc_html(request: Request):
    """ReDoc documentation"""
    base_route = get_base_route_http()
    return get_redoc_html(
        openapi_url=f"{base_route}/openapi.json",
        title=app.title + " - ReDoc"
    )


@api_router.get("/openapi.json", include_in_schema=False)
async def openapi():
    """OpenAPI schema"""
    base_route = get_base_route_http()
    return get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        servers=[{"url": base_route}] if base_route else None
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "5000"))
    host = os.getenv("HOST", "0.0.0.0")
    logger.info(f"Starting API server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
