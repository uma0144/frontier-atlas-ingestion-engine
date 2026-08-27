"""
Date normalization and freshness engine.
Handles ISO 8601, RFC 2822, relative strings ('2 hours ago'), and strict 24-hour verification.
"""

import re
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from typing import Optional, Tuple
import logging

logger = logging.getLogger("DateParser")


def parse_flexible_date(date_str: Optional[str]) -> Optional[datetime]:
    """
    Parse any date representation (relative, RFC 2822, ISO-8601, standard formats)
    into a timezone-aware UTC datetime.
    """
    if not date_str or not isinstance(date_str, str):
        return None

    cleaned = date_str.strip()
    now_utc = datetime.now(timezone.utc)

    # 1. Handle Relative Dates
    # e.g., "just now", "moments ago"
    if re.search(r'\b(just now|moments ago|seconds? ago)\b', cleaned, re.I):
        return now_utc

    # e.g., "2 hours ago", "4h ago", "45 mins ago", "1 day ago"
    rel_match = re.search(r'(\d+)\s*(sec|second|min|minute|hr|hour|d|day)s?\s*ago', cleaned, re.I)
    if rel_match:
        amount = int(rel_match.group(1))
        unit = rel_match.group(2).lower()
        if "sec" in unit:
            return now_utc - timedelta(seconds=amount)
        elif "min" in unit:
            return now_utc - timedelta(minutes=amount)
        elif "hr" in unit or "hour" in unit:
            return now_utc - timedelta(hours=amount)
        elif "d" in unit or "day" in unit:
            return now_utc - timedelta(days=amount)

    # e.g., "yesterday"
    if "yesterday" in cleaned.lower():
        return now_utc - timedelta(days=1)

    # e.g., "today"
    if "today" in cleaned.lower():
        return now_utc

    # 2. Try RFC 2822 (Common in RSS feeds: "Thu, 27 Aug 2026 14:20:00 +0000")
    try:
        dt = parsedate_to_datetime(cleaned)
        if dt:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
    except Exception:
        pass

    # 3. Try ISO-8601
    try:
        iso_clean = cleaned.replace("Z", "+00:00")
        dt = datetime.fromisoformat(iso_clean)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass

    # 4. Standard Date Patterns
    date_patterns = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d %B %Y",
        "%d %b %Y",
        "%Y/%m/%d",
        "%m/%d/%Y",
    ]
    for pattern in date_patterns:
        try:
            dt = datetime.strptime(cleaned, pattern)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    return None


def is_within_last_24_hours(dt: Optional[datetime], tolerance_hours: float = 24.0) -> bool:
    """Check whether a datetime is strictly within the last 24 hours."""
    if not dt:
        return False
    now_utc = datetime.now(timezone.utc)
    # Handle slight clock drift or future scheduled posts (up to 1 hour in future)
    diff = now_utc - dt
    diff_hours = diff.total_seconds() / 3600.0
    return -1.0 <= diff_hours <= tolerance_hours


def format_iso8601(dt: Optional[datetime]) -> str:
    """Format datetime object into clean ISO-8601 string."""
    if dt is None:
        dt = datetime.now(timezone.utc)
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()
