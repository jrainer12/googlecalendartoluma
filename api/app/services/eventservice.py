#!/usr/bin/env python3
"""
Event service for processing calendar events and building payloads.
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pytz
from icalendar import Calendar
import aiofiles

from app.services.calendarservice import embed_to_ics, load_ics
from app.services.payloadbuilder import _to_dt, build_payload, _slugify_filename

logger = logging.getLogger(__name__)


def next_upcoming_events(cal: Calendar, tzname: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Extract upcoming events from calendar.
    
    Args:
        cal: Parsed Calendar object
        tzname: Timezone name for local time comparison
        limit: Maximum number of events to return
        
    Returns:
        List of event dictionaries with summary, description, location, start_utc, end_utc
    """
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


async def fetch_events(
    gcal_embed_url: str,
    luma_calendar_api_id: str,
    timezone_name: str,
    limit: int,
    cover_url: str,
    tint_color: str,
    font_title: str,
    out_dir: str = "luma_payloads"
) -> Dict[str, Any]:
    """
    Fetch and process events from Google Calendar.
    
    Args:
        gcal_embed_url: Google Calendar embed URL
        luma_calendar_api_id: Luma calendar API ID
        timezone_name: Timezone name
        limit: Maximum number of events to fetch
        cover_url: Cover image URL
        tint_color: Tint color for events
        font_title: Font title for events
        out_dir: Output directory for saved payloads
        
    Returns:
        Dictionary with success, count, events, timezone, or error
    """
    try:
        logger.info("Fetching Google Calendar events")
        os.makedirs(out_dir, exist_ok=True)

        ics_url, tzname = embed_to_ics(gcal_embed_url, timezone_name)
        cal = await load_ics(ics_url)
        events = next_upcoming_events(cal, tzname, limit=limit)
        logger.info(f"Found {len(events)} upcoming event(s)")

        payloads = []
        for idx, ev in enumerate(events, start=1):
            logger.info(f"Processing event {idx}: {ev['summary']}")
            payload = build_payload(
                ev,
                tzname,
                luma_calendar_api_id,
                cover_url,
                tint_color,
                font_title
            )
            payloads.append(payload)

            base_slug = _slugify_filename(ev["summary"])
            filename = f"{base_slug}.json"
            out_path = os.path.join(out_dir, filename)
            if os.path.exists(out_path):
                filename = f"{base_slug}-{idx}.json"
                out_path = os.path.join(out_dir, filename)
            
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

