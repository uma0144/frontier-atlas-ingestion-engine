"""
Unit tests for date parsing and freshness filter.
"""

from datetime import datetime, timezone, timedelta
from src.utils.date_parser import parse_flexible_date, is_within_last_24_hours, format_iso8601


def test_relative_date_parsing():
    now_utc = datetime.now(timezone.utc)

    # 2 hours ago
    dt_2h = parse_flexible_date("2 hours ago")
    assert dt_2h is not None
    assert is_within_last_24_hours(dt_2h) is True
    assert abs((now_utc - dt_2h).total_seconds() - 7200) < 60

    # 45 minutes ago
    dt_45m = parse_flexible_date("45 minutes ago")
    assert dt_45m is not None
    assert is_within_last_24_hours(dt_45m) is True

    # 5 days ago (should be stale)
    dt_old = parse_flexible_date("5 days ago")
    assert dt_old is not None
    assert is_within_last_24_hours(dt_old) is False


def test_rfc2822_parsing():
    rfc_date = "Thu, 27 Aug 2026 14:00:00 +0000"
    dt = parse_flexible_date(rfc_date)
    assert dt is not None
    assert dt.year == 2026
    assert dt.month == 8


def test_iso_parsing():
    iso_date = "2026-08-27T10:15:30Z"
    dt = parse_flexible_date(iso_date)
    assert dt is not None
    assert dt.hour == 10
    iso_str = format_iso8601(dt)
    assert "2026-08-27" in iso_str
