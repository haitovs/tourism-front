# app/services/agenda.py
from __future__ import annotations

from datetime import date as _date  # ← add this
from datetime import datetime as _dt
from typing import List, Optional

from fastapi import Request

from app.core.http import api_get

DAYS_PATH = "/agenda/days"
DAY_EPISODES_PATH = "/agenda/day/{day_id}/episodes"


def _to_date(val):
    """Accept date, datetime, or ISO string -> return a date object."""
    if isinstance(val, _date) and not isinstance(val, _dt):
        return val
    if isinstance(val, _dt):
        return val.date()
    if isinstance(val, str):
        s = val.strip().replace("Z", "")
        # handle 'YYYY-MM-DDTHH:MM:SS' or 'YYYY-MM-DD HH:MM:SS'
        if "T" in s:
            s = s.split("T", 1)[0]
        elif " " in s:
            s = s.split(" ", 1)[0]
        try:
            return _date.fromisoformat(s)  # 'YYYY-MM-DD'
        except Exception:
            pass
    return None


def _normalize_day(row: dict) -> dict:
    d = _to_date(row.get("date"))
    return {
        "id": row.get("id"),
        "date": d or row.get("date"),  # ensure templates get a date when possible
        "label": row.get("label") or row.get("title") or "",
        "published": bool(row.get("published", True)),
        "sort_order": row.get("sort_order"),
        "site_id": row.get("site_id"),
    }


def _normalize_episode(row: dict) -> dict:
    return row


async def list_days(req: Request, *, site_id: Optional[int] = None, only_published: bool = True) -> List[dict]:
    params = {}
    if site_id is not None:
        params["site_id"] = site_id
    if only_published:
        params["published"] = "true"
    rows = await api_get(req, DAYS_PATH, params=params) or []
    return [_normalize_day(r) for r in rows]


async def list_episodes_for_day(req: Request, *, day_id: int, site_id: Optional[int] = None, only_published: bool = True) -> List[dict]:
    params = {}
    if site_id is not None:
        params["site_id"] = site_id
    if only_published:
        params["published"] = "true"
    rows = await api_get(req, DAY_EPISODES_PATH.format(day_id=day_id), params=params) or []
    return [_normalize_episode(r) for r in rows]
