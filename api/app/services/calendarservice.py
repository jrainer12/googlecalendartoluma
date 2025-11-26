#!/usr/bin/env python3
"""
Calendar service for fetching and processing Google Calendar ICS data.
"""
import logging
from typing import Tuple
from urllib.parse import urlparse, parse_qs, unquote
from icalendar import Calendar
import httpx

logger = logging.getLogger(__name__)


def embed_to_ics(embed_url: str, default_timezone: str = "America/New_York") -> Tuple[str, str]:
    """
    Convert Google Calendar embed URL to ICS URL.
    
    Args:
        embed_url: Google Calendar embed URL
        default_timezone: Default timezone if not specified in URL
        
    Returns:
        Tuple of (ics_url, timezone)
    """
    qs = parse_qs(urlparse(embed_url).query)
    src = qs.get("src", [None])[0]
    ctz = qs.get("ctz", [default_timezone])[0]
    if not src:
        raise ValueError("No 'src' in embed URL")
    cal_id = unquote(src)
    ics_url = f"https://calendar.google.com/calendar/ical/{cal_id}/public/full.ics"
    return ics_url, ctz


async def load_ics(ics_url: str) -> Calendar:
    """
    Fetch and parse ICS calendar from URL.
    
    Args:
        ics_url: URL to the ICS calendar file
        
    Returns:
        Parsed Calendar object
        
    Raises:
        httpx.HTTPError: If the HTTP request fails
    """
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

