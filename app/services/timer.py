# services/timer.py
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

MONTHS_UPPER = ["JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER"]


def _safe_zoneinfo(tz_name: str, fallback: str = "UTC"):
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        try:
            return ZoneInfo(fallback)
        except ZoneInfoNotFoundError:
            return timezone.utc


def build_timer_context(deadline_dt: datetime, display_tz: str = "Asia/Ashgabat") -> dict:
    import logging
    log = logging.getLogger("services.timer")

    tz = _safe_zoneinfo(display_tz)

    # If naive, interpret as display timezone to avoid accidental UTC drift
    try:
        if deadline_dt.tzinfo is None:
            deadline_dt = deadline_dt.replace(tzinfo=tz)
        local_deadline = deadline_dt.astimezone(tz)
    except Exception as e:
        log.warning("build_timer_context timezone conversion failed: %r", e)
        local_deadline = deadline_dt

    # Be defensive with month index
    try:
        month_index = max(1, min(12, int(local_deadline.month)))
    except Exception:
        month_index = 1
    month_upper = MONTHS_UPPER[month_index - 1]

    try:
        day_num = int(local_deadline.day)
    except Exception:
        day_num = 1

    try:
        deadline_utc_iso = deadline_dt.astimezone(timezone.utc).isoformat()
    except Exception:
        deadline_utc_iso = deadline_dt.isoformat()

    return {
        "deadline_iso_utc": deadline_utc_iso,
        "deadline_month_upper": month_upper,
        "deadline_day": day_num,
    }


def get_deadline_from_settings(settings) -> datetime:
    import logging
    from datetime import datetime
    log = logging.getLogger("services.timer")

    raw = getattr(settings, "EVENT_DEADLINE", None)
    if not raw:
        return datetime(2025, 8, 25, 18, 0, 0)

    try:
        s = str(raw).strip()
        if s.endswith("Z"):
            s = s.replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    except Exception as e:
        log.warning("get_deadline_from_settings: failed to parse %r (%r), using default", raw, e)
        return datetime(2025, 8, 25, 18, 0, 0)
