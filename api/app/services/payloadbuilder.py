#!/usr/bin/env python3
"""
Payload builder for converting calendar events to Luma-compatible JSON payloads.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any


def _to_dt(v):
    """Convert iCalendar date/datetime to Python datetime."""
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
    """Convert datetime to ISO8601 format with milliseconds and Z suffix."""
    base = dt_utc.replace(microsecond=0).isoformat()
    base = base.replace("+00:00", "")
    return f"{base}.000Z"


def duration_from_range(start: datetime, end: datetime) -> str:
    """Convert time range to ISO8601 duration format."""
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


def make_pm_paragraph(text: str) -> Dict[str, Any]:
    """Create a ProseMirror paragraph node."""
    return {"type": "paragraph", "content": [{"type": "text", "text": text}]}


def to_prosemirror_doc(desc_text: str, location_text: str) -> Optional[Dict[str, Any]]:
    """Convert description and location to ProseMirror document format."""
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


def build_geo_address(location_text: str) -> Optional[Dict[str, Any]]:
    """Build geo address object from location text."""
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


def build_payload(
    ev: Dict[str, Any],
    tzname: str,
    calendar_api_id: str,
    cover_url: str,
    tint_color: str,
    font_title: str
) -> Dict[str, Any]:
    """
    Build Luma-compatible event payload from event data.
    
    Args:
        ev: Event dictionary with summary, description, location, start_utc, end_utc
        tzname: Timezone name
        calendar_api_id: Luma calendar API ID
        cover_url: Cover image URL
        tint_color: Tint color for the event
        font_title: Font title for the event
        
    Returns:
        Complete event payload dictionary
    """
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
        "cover_url": cover_url,
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
        "tint_color": tint_color,
        "font_title": font_title,
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


def _slugify_filename(name: str) -> str:
    """Convert event name to a slug suitable for filename."""
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

