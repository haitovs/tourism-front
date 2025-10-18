# services/timer.py
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

MONTHS_UPPER = ["JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER"]


def _safe_zoneinfo(tz_name: str, fallback: str = "UTC"):
    """
    Try to load tz_name; if not found (e.g., Windows without tzdata),
    try fallback; if that also fails, use timezone.utc.
    """
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        try:
            return ZoneInfo(fallback)
        except ZoneInfoNotFoundError:
            return timezone.utc


def build_timer_context(deadline_dt: datetime, display_tz: str = "Asia/Ashgabat") -> dict:
    """
    Returns template-ready countdown fields.
    - Accepts naive or aware datetime.
    - Always outputs deadline in UTC ISO (for JS), labels in display_tz when possible.
    """
    tz = _safe_zoneinfo(display_tz)

    if deadline_dt.tzinfo is None:
        deadline_dt = deadline_dt.replace(tzinfo=tz)

    # Labels (month/day) should reflect the display timezone
    local_deadline = deadline_dt.astimezone(tz)
    month_upper = MONTHS_UPPER[local_deadline.month - 1]
    day_num = local_deadline.day

    # JS reads a UTC ISO string to avoid client-TZ drift
    deadline_utc_iso = deadline_dt.astimezone(timezone.utc).isoformat()

    return {
        "deadline_iso_utc": deadline_utc_iso,
        "deadline_month_upper": month_upper,
        "deadline_day": day_num,
    }


def get_deadline_from_settings(settings) -> datetime:
    """
    Expects settings.EVENT_DEADLINE like:
      '2025-08-25T18:00:00+05:00'  (preferred, with offset)
    or '2025-08-25T18:00:00'       (naive; will be assumed in display TZ later)
    """
    # Prefer ISO parsing with offset if available
    try:
        return datetime.fromisoformat(settings.EVENT_DEADLINE)
    except Exception:
        # Fallback hardcoded example (adjust to your real date)
        return datetime(2025, 8, 25, 18, 0, 0)
