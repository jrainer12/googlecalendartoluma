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
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
import yaml
from pathlib import Path as PathlibPath

from app.util.config import config, get_logging_level, get_base_route_http
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


def get_base_route_sync() -> str:
    """Get base route synchronously from environment variable, YAML file, or default.
    Used for setting docs_url at app creation time before config loads."""
    # Check environment variable first
    env_value = os.getenv('APP_BASE_ROUTE_HTTP')
    if env_value:
        return env_value
    
    # Try to read from YAML file synchronously
    try:
        resources_path = PathlibPath(__file__).parent / "resources"
        app_yaml = resources_path / "application.yaml"
        if app_yaml.exists():
            with open(app_yaml, 'r') as f:
                yaml_data = yaml.safe_load(f) or {}
                base_route = yaml_data.get('app', {}).get('base_route_http')
                if base_route:
                    return base_route
    except Exception as e:
        logger.debug(f"Could not read base_route from YAML synchronously: {e}")
    
    # Default fallback
    return '/backend/luma-syncer'


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup - wrap in try/except to ensure app starts even if config fails
    try:
        await config.load_config()
        
        # Update logging level after config is loaded
        log_level = getattr(logging, get_logging_level().upper(), logging.INFO)
        logging.getLogger().setLevel(log_level)
        
        # Add filter to suppress health check access logs
        class HealthCheckFilter(logging.Filter):
            def filter(self, record):
                # Filter out health check access logs
                message = record.getMessage()
                return "/health" not in message and '"GET /health' not in message
        
        # Apply filter to uvicorn access logger
        access_logger = logging.getLogger("uvicorn.access")
        # Remove existing filters to avoid duplicates
        access_logger.filters = [f for f in access_logger.filters if not isinstance(f, HealthCheckFilter)]
        access_logger.addFilter(HealthCheckFilter())
        
        # Log the active profile
        deployment_profile = os.getenv('DEPLOYMENT_PROFILE', 'dev')
        logger.info(f"Profile {deployment_profile} activated.")
        
        # Check if debug mode is enabled and log if so
        debug_mode = config.get_bool("app.debug", False) or (log_level == logging.DEBUG)
        if debug_mode:
            logger.debug("Debug mode has been activated")
        
        # Get base route and mount the API router with prefix
        base_route = get_base_route_http()
        # Mount router with prefix - all routes will be under base_route
        app.include_router(api_router, prefix=base_route)
        
        logger.info(f"Application started with logging level: {log_level}")
        logger.info(f"API routes mounted at base path: {base_route}")
        logger.info(f"Swagger docs available at: {base_route}/docs")
        logger.info(f"ReDoc available at: {base_route}/redoc")
    except Exception as e:
        logger.error(f"Error during startup: {e}", exc_info=True)
        # Still try to mount router with default base route
        try:
            base_route = os.getenv('APP_BASE_ROUTE_HTTP', '/backend/luma-syncer')
            app.include_router(api_router, prefix=base_route)
            logger.warning(f"Using default base route: {base_route}")
        except Exception as e2:
            logger.error(f"Failed to mount router: {e2}", exc_info=True)
    
    # Log all registered routes for debugging
    routes = [f"{route.path} ({route.methods})" for route in app.routes if hasattr(route, 'path')]
    logger.info(f"Registered routes: {routes}")
    logger.info(f"Health endpoint available at: /health")
    
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

# Middleware to suppress access logs for health checks
class SuppressHealthCheckLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to suppress access logging for health check endpoints."""
    
    async def dispatch(self, request: StarletteRequest, call_next):
        # Check if this is a health check request
        is_health_check = request.url.path in ["/health", "/health/"]
        
        # If it's a health check, temporarily disable access logging
        if is_health_check:
            # Get the uvicorn access logger
            access_logger = logging.getLogger("uvicorn.access")
            original_level = access_logger.level
            # Temporarily set to WARNING to suppress INFO logs
            access_logger.setLevel(logging.WARNING)
            try:
                response = await call_next(request)
                return response
            finally:
                # Restore original log level
                access_logger.setLevel(original_level)
        else:
            return await call_next(request)

# Add middleware to suppress health check logging (before CORS)
app.add_middleware(SuppressHealthCheckLoggingMiddleware)

# Enable CORS for API access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- CONFIG ----------
# Read from environment variables with fallback to defaults
GCAL_EMBED_URL = os.getenv(
    "GCAL_EMBED_URL",
    "https://calendar.google.com/calendar/embed?src=tnti8oguf84qd354budk86vdpk%40group.calendar.google.com&ctz=America%2FNew_York"
)
LUMA_CALENDAR_API_ID = os.getenv("LUMA_CALENDAR_API_ID", "cal-iPlAn4RA1wD1lDh")

# Match your latest example exactly (change if you like)
COVER_URL = os.getenv(
    "COVER_URL",
    "https://images.lumacdn.com/gallery-images/vn/e95edc2d-7ad2-45a0-ba4c-393e17cb8f60"
)
TINT_COLOR = os.getenv("TINT_COLOR", "#708967")
FONT_TITLE = os.getenv("FONT_TITLE", "geist-mono")

TIMEZONE_NAME = os.getenv("TIMEZONE_NAME", "America/New_York")
LIMIT = int(os.getenv("LIMIT", "5"))
OUT_DIR = os.getenv("OUT_DIR", "luma_payloads")
# ----------------------------


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
    result = await fetch_events(
        gcal_embed_url=GCAL_EMBED_URL,
        luma_calendar_api_id=LUMA_CALENDAR_API_ID,
        timezone_name=TIMEZONE_NAME,
        limit=LIMIT,
        cover_url=COVER_URL,
        tint_color=TINT_COLOR,
        font_title=FONT_TITLE,
        out_dir=OUT_DIR
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
    result = await fetch_events(
        gcal_embed_url=GCAL_EMBED_URL,
        luma_calendar_api_id=LUMA_CALENDAR_API_ID,
        timezone_name=TIMEZONE_NAME,
        limit=LIMIT,
        cover_url=COVER_URL,
        tint_color=TINT_COLOR,
        font_title=FONT_TITLE,
        out_dir=OUT_DIR
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
    from uvicorn.config import LOGGING_CONFIG
    
    # Custom logging config to suppress health check access logs
    log_config = LOGGING_CONFIG.copy()
    
    # Add a filter to the access logger to exclude health checks
    class HealthCheckFilter(logging.Filter):
        def filter(self, record):
            # Filter out health check access logs
            return "/health" not in record.getMessage()
    
    # Apply filter to uvicorn access logger
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.addFilter(HealthCheckFilter())
    
    port = int(os.getenv("PORT", "5000"))
    host = os.getenv("HOST", "0.0.0.0")
    logger.info(f"Starting API server on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_config=log_config)
