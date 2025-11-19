#!/usr/bin/env python3
# API server for Google Calendar to Luma sync
import os, json, pytz, sys, logging
from urllib.parse import urlparse, parse_qs, unquote
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from contextlib import asynccontextmanager
from icalendar import Calendar
import httpx
import aiofiles
from fastapi import FastAPI, HTTPException, status, Path, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from util.config import config, get_logging_level, get_base_route_http

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
        import yaml
        from pathlib import Path
        resources_path = Path(__file__).parent / "resources"
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
        
        # Log the active profile
        deployment_profile = os.getenv('DEPLOYMENT_PROFILE', 'dev')
        logger.info(f"Profile {deployment_profile} activated.")
        
        # Check if debug mode is enabled and log if so
        debug_mode = config.get_bool("app.debug", False) or (log_level == logging.DEBUG)
        if debug_mode:
            logger.debug("Debug mode has been activated")
        
        # Get base route and mount the API router
        base_route = get_base_route_http()
        app.include_router(api_router, prefix=base_route)
        
        # Note: docs_url and redoc_url are set at app creation time and cannot be changed
        # They are set to use the base route from environment variable or default
        
        logger.info(f"Application started with logging level: {log_level}")
        logger.info(f"API routes mounted at base path: {base_route}")
        logger.info(f"Swagger docs available at: {app.docs_url}")
        logger.info(f"ReDoc available at: {app.redoc_url}")
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


# Get base route synchronously for docs URLs and root_path (before config loads)
# This will be overridden with actual config value in lifespan handler if different
_base_route_sync = get_base_route_sync()

# Create main FastAPI app with lifespan handler
# root_path is required when behind a reverse proxy with a path prefix
# This ensures Swagger UI generates correct URLs
app = FastAPI(
    title="Google Calendar to Luma Sync API",
    description="REST API that exposes Google Calendar events as Luma-compatible JSON payloads",
    version="1.0.0",
    root_path=_base_route_sync,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

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
DIVIDER = "=" * 60
# ----------------------------

# ---------- PYDANTIC MODELS ----------
class HealthResponse(BaseModel):
    status: str = Field(..., description="Health status of the API")

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

class GeoAddress(BaseModel):
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
    type: str = "free"
    ethereum_token_requirements: List[dict] = []
    cents: Optional[int] = None
    is_flexible: bool = False
    min_cents: Optional[int] = None
    require_approval: bool = False
    currency: Optional[str] = None
    is_hidden: bool = False

class EventPayload(BaseModel):
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
    success: bool = Field(..., description="Whether the operation was successful")
    event: EventPayload = Field(..., description="The event payload")

class EventsResponse(BaseModel):
    success: bool = Field(..., description="Whether the operation was successful")
    count: int = Field(..., description="Number of events returned")
    events: List[EventPayload] = Field(..., description="List of event payloads")
    timezone: str = Field(..., description="Timezone used for event processing")

class ErrorResponse(BaseModel):
    success: bool = False
    error: str = Field(..., description="Error message")

class APIInfoResponse(BaseModel):
    service: str = "Google Calendar to Luma Sync API"
    version: str = "1.0.0"
    endpoints: dict = Field(..., description="Available API endpoints")
# -------------------------------------


def _slugify_filename(name: str) -> str:
    name = (name or "").strip().lower()
    if not name:
        return "event"
    chars = []
    for ch in name:
        if ch.isalnum():
            chars.append(ch)
        elif ch in (" ", "-", "_"):
            chars.append("-")
    slug = "".join(chars)
    while "--" in slug:
        slug = slug.replace("--", "-")
    slug = slug.strip("-")
    return slug or "event"


def embed_to_ics(embed_url: str):
    qs = parse_qs(urlparse(embed_url).query)
    src = qs.get("src", [None])[0]
    ctz = qs.get("ctz", [TIMEZONE_NAME])[0]
    if not src:
        raise ValueError("No 'src' in embed URL")
    cal_id = unquote(src)
    ics_url = f"https://calendar.google.com/calendar/ical/{cal_id}/public/full.ics"
    return ics_url, ctz


async def load_ics(ics_url: str) -> Calendar:
    logger.info(f"Fetching ICS from: {ics_url}")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(ics_url)
            r.raise_for_status()
            logger.info("Successfully fetched ICS calendar")
            return Calendar.from_ical(r.content)
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch ICS calendar: {e}")
        raise


def _to_dt(v):
    if hasattr(v, "dt"):
        v = v.dt
    is_all_day = False
    if isinstance(v, datetime):
        dt = v if v.tzinfo else v.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc), is_all_day
    # all-day date
    is_all_day = True
    dt = datetime(v.year, v.month, v.day, 0, 0, tzinfo=timezone.utc)
    return dt, is_all_day


def iso8601_z_with_ms(dt_utc: datetime) -> str:
    base = dt_utc.replace(microsecond=0).isoformat()
    base = base.replace("+00:00", "")
    return f"{base}.000Z"


def duration_from_range(start: datetime, end: datetime) -> str:
    seconds = int((end - start).total_seconds())
    if seconds <= 0:
        seconds = 3600
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    out = "PT"
    if h:
        out += f"{h}H"
    if m:
        out += f"{m}M"
    if s or (not h and not m):
        out += f"{s}S"
    return out


def next_upcoming_events(cal: Calendar, tzname: str, limit=5):
    local_tz = pytz.timezone(tzname)
    now_local = datetime.now(local_tz)
    upcoming = []
    for comp in cal.walk():
        if comp.name != "VEVENT":
            continue
        dtstart_raw = comp.get("dtstart")
        if not dtstart_raw:
            continue
        start_utc, all_day = _to_dt(dtstart_raw)
        dtend_raw = comp.get("dtend")
        if dtend_raw:
            end_utc, _ = _to_dt(dtend_raw)
        else:
            end_utc = start_utc + (timedelta(days=1) if all_day else timedelta(hours=1))
        if start_utc.astimezone(local_tz) < now_local:
            continue
        upcoming.append({
            "summary": str(comp.get("summary") or "(untitled)"),
            "description": str(comp.get("description") or ""),
            "location": str(comp.get("location") or ""),
            "start_utc": start_utc,
            "end_utc": end_utc
        })
    upcoming.sort(key=lambda x: x["start_utc"])
    return upcoming[:limit]


def make_pm_paragraph(text: str):
    return {"type": "paragraph", "content": [{"type": "text", "text": text}]}


def to_prosemirror_doc(desc_text: str, location_text: str):
    content = []
    desc_text = (desc_text or "").strip()
    if desc_text:
        for line in desc_text.splitlines():
            line = line.rstrip()
            if line:
                content.append(make_pm_paragraph(line))
            else:
                content.append({"type": "paragraph"})
    if location_text:
        content.append(make_pm_paragraph(f"Location: {location_text.strip()}"))
    if not content:
        return None
    return {"type": "doc", "content": content}


def build_geo_address(location_text: str):
    if not location_text:
        return None
    loc = location_text.strip()
    return {
        "description": "",
        "full_address": loc,
        "city_state": None,
        "type": "text",
        "address": loc,
        "place_id": None,
        "city": None,
        "country": None,
        "country_code": None,
        "region": None
    }


def build_payload(ev, tzname, calendar_api_id):
    pm_doc = to_prosemirror_doc(ev["description"], ev["location"])

    payload = {
        "name": ev["summary"],
        "start_at": iso8601_z_with_ms(ev["start_utc"]),
        "duration_interval": duration_from_range(ev["start_utc"], ev["end_utc"]),
        "zoom_meeting_url": None,
        "zoom_meeting_id": None,
        "zoom_meeting_password": None,
        "description_mirror": pm_doc,
        "geo_address_visibility": "public",
        "cover_url": COVER_URL,
        "zoom_session_type": None,
        "zoom_creation_method": None,
        "location_type": "offline",
        "geo_address_json": build_geo_address(ev["location"]),
        "coordinate": None,
        "timezone": tzname,
        "calendar_api_id": calendar_api_id,
        "calendar_to_submit_to_api_id": None,
        "supports_members_only": False,
        "max_capacity": None,
        "waitlist_enabled": False,
        "visibility": "public",
        "theme_meta": {"theme": "legacy"},
        "tint_color": TINT_COLOR,
        "font_title": FONT_TITLE,
        "ticket_types": [
            {
                "type": "free",
                "ethereum_token_requirements": [],
                "cents": None,
                "is_flexible": False,
                "min_cents": None,
                "require_approval": False,
                "currency": None,
                "is_hidden": False
            }
        ],
    }
    return payload


async def fetch_events():
    """Fetch and process events from Google Calendar"""
    try:
        logger.info("Fetching Google Calendar events")
        os.makedirs(OUT_DIR, exist_ok=True)

        ics_url, tzname = embed_to_ics(GCAL_EMBED_URL)
        cal = await load_ics(ics_url)
        events = next_upcoming_events(cal, tzname, limit=LIMIT)
        logger.info(f"Found {len(events)} upcoming event(s)")

        payloads = []
        for idx, ev in enumerate(events, start=1):
            logger.info(f"Processing event {idx}: {ev['summary']}")
            payload = build_payload(ev, tzname, LUMA_CALENDAR_API_ID)
            payloads.append(payload)

            base_slug = _slugify_filename(ev["summary"])
            filename = f"{base_slug}.json"
            out_path = os.path.join(OUT_DIR, filename)
            if os.path.exists(out_path):
                filename = f"{base_slug}-{idx}.json"
                out_path = os.path.join(OUT_DIR, filename)
            
            # Async file write
            async with aiofiles.open(out_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(payload, ensure_ascii=False, indent=2))
            logger.info(f"Saved payload to {out_path}")

        return {
            "success": True,
            "count": len(payloads),
            "events": payloads,
            "timezone": tzname
        }
    except Exception as e:
        logger.error(f"Error fetching events: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


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
    result = await fetch_events()
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
    result = await fetch_events()
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


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "5000"))
    host = os.getenv("HOST", "0.0.0.0")
    logger.info(f"Starting API server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)

