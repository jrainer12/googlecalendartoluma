#!/usr/bin/env python3
# make_luma_event_payloads.py
import os, json, requests, pytz, sys, logging
from urllib.parse import urlparse, parse_qs, unquote
from datetime import datetime, timezone, timedelta
from icalendar import Calendar

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ---------- CONFIG ----------
# Read from environment variables with fallback to defaults
GCAL_EMBED_URL = os.getenv(
    "GCAL_EMBED_URL",
    "https://calendar.google.com/calendar/embed?src=tnti8oguf84qd354budk86vdpk%40group.calendar.google.com&ctz=America%2FNew_York"
)
LUMA_CALENDAR_API_ID = os.getenv("LUMA_CALENDAR_API_ID", "cal-iPlAn4RA1wD1lDh")

# Match your latest example exactly (change if you like)
COVER_URL   = os.getenv(
    "COVER_URL",
    "https://images.lumacdn.com/gallery-images/vn/e95edc2d-7ad2-45a0-ba4c-393e17cb8f60"
)
TINT_COLOR  = os.getenv("TINT_COLOR", "#708967")
FONT_TITLE  = os.getenv("FONT_TITLE", "geist-mono")

TIMEZONE_NAME = os.getenv("TIMEZONE_NAME", "America/New_York")
LIMIT = int(os.getenv("LIMIT", "5"))
OUT_DIR = os.getenv("OUT_DIR", "luma_payloads")
DIVIDER = "=" * 60
# ----------------------------

def embed_to_ics(embed_url: str):
    qs = parse_qs(urlparse(embed_url).query)
    src = qs.get("src", [None])[0]
    ctz = qs.get("ctz", [TIMEZONE_NAME])[0]
    if not src:
        raise ValueError("No 'src' in embed URL")
    cal_id = unquote(src)
    ics_url = f"https://calendar.google.com/calendar/ical/{cal_id}/public/full.ics"
    return ics_url, ctz

def load_ics(ics_url: str) -> Calendar:
    logger.info(f"Fetching ICS from: {ics_url}")
    try:
        r = requests.get(ics_url, timeout=30)
        r.raise_for_status()
        logger.info("Successfully fetched ICS calendar")
        return Calendar.from_ical(r.content)
    except requests.RequestException as e:
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
    if h: out += f"{h}H"
    if m: out += f"{m}M"
    if s or (not h and not m): out += f"{s}S"
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
        # future filter in local tz
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

# ----- ProseMirror helpers -----
def make_pm_paragraph(text: str):
    return {"type": "paragraph", "content": [{"type": "text", "text": text}]}

def to_prosemirror_doc(desc_text: str, location_text: str):
    """
    Build a ProseMirror doc like your sample:
    {"type":"doc","content":[ {"type":"paragraph","content":[{"type":"text","text":"line"}]}, ... ]}
    """
    content = []
    desc_text = (desc_text or "").strip()
    if desc_text:
        for line in desc_text.splitlines():
            line = line.rstrip()
            if line:
                content.append(make_pm_paragraph(line))
            else:
                # preserve blank line as empty paragraph
                content.append({"type": "paragraph"})
    if location_text:
        content.append(make_pm_paragraph(f"Location: {location_text.strip()}"))
    if not content:
        return None
    return {"type": "doc", "content": content}

def build_geo_address(location_text: str):
    """
    Build the geo_address_json skeleton required by your example.
    Without geocoding, we set the fields we don't know to null.
    """
    if not location_text:
        return None
    loc = location_text.strip()
    return {
        "description": "",
        "full_address": loc,
        "city_state": None,
        "type": "text",          # we don't have Google Places here; mark as text
        "address": loc,
        "place_id": None,
        "city": None,
        "country": None,
        "country_code": None,
        "region": None
    }

def build_payload(ev, tzname, calendar_api_id):
    # ProseMirror description (from event description + appended "Location: ...")
    pm_doc = to_prosemirror_doc(ev["description"], ev["location"])

    payload = {
        "name": ev["summary"],
        "start_at": iso8601_z_with_ms(ev["start_utc"]),
        "duration_interval": duration_from_range(ev["start_utc"], ev["end_utc"]),
        "zoom_meeting_url": None,
        "zoom_meeting_id": None,
        "zoom_meeting_password": None,
        "description_mirror": pm_doc,  # ProseMirror object or null
        "geo_address_visibility": "public",
        "cover_url": COVER_URL,
        "zoom_session_type": None,
        "zoom_creation_method": None,
        "location_type": "offline",    # hardcoded per your request
        "geo_address_json": build_geo_address(ev["location"]),  # or null if none
        "coordinate": None,            # no geocoding here
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

def main():
    try:
        logger.info("Starting Google Calendar to Luma sync")
        os.makedirs(OUT_DIR, exist_ok=True)
        logger.info(f"Output directory: {OUT_DIR}")
        
        ics_url, tzname = embed_to_ics(GCAL_EMBED_URL)
        logger.info(f"Using timezone: {tzname}")
        
        cal = load_ics(ics_url)
        events = next_upcoming_events(cal, tzname, limit=LIMIT)
        logger.info(f"Found {len(events)} upcoming event(s)")

        if not events:
            logger.warning("No upcoming events found.")
            return

        for idx, ev in enumerate(events, start=1):
            logger.info(f"Processing event {idx}: {ev['summary']}")
            payload = build_payload(ev, tzname, LUMA_CALENDAR_API_ID)

            # Save to file
            out_path = os.path.join(OUT_DIR, f"event_{idx}.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved payload to {out_path}")

            # Print & divider
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            if idx < len(events):
                print("\n" + DIVIDER + "\n")

        logger.info("Processing complete")
        print("\n---")
        print("Send one event (example for event_1.json) with Content-Type: application/json:")
        print(f"""curl 'https://api2.luma.com/event/create' \\
  -H 'content-type: application/json' \\
  -H 'accept: */*' \\
  -H 'origin: https://luma.com' \\
  -H 'referer: https://luma.com/' \\
  -H 'x-luma-client-type: luma-web' \\
  -b 'YOUR_FRESH_LUMA_COOKIES_HERE' \\
  --data-binary '@{OUT_DIR}/event_1.json'""")
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
