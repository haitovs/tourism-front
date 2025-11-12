# app/services/statistics.py
from __future__ import annotations

from typing import Optional

from fastapi import Request

from app.core.http import api_get
from app.utils.timed_cache import TimedCache

_STATS_CACHE = TimedCache(ttl_seconds=30.0)


def _project(payload: dict | None) -> dict:
    def _to_int(value):
        try:
            return int(value or 0)
        except Exception:
            return 0

    payload = payload or {}
    return {
        "episodes": _to_int(payload.get("episodes") or payload.get("sessions")),
        "delegates": _to_int(payload.get("delegates")),
        "speakers": _to_int(payload.get("speakers")),
        "companies": _to_int(payload.get("companies") or payload.get("participants")),
    }


def _extract_row(data) -> dict:
    if isinstance(data, dict):
        for key in ("data", "item", "statistics"):
            if isinstance(data.get(key), dict):
                return data[key]
        if isinstance(data.get("items"), list) and data["items"]:
            return data["items"][0]
        return data
    if isinstance(data, list) and data:
        return data[0]
    return {}


async def get_statistics(req: Request, site_id: Optional[int] = None) -> dict:
    cache_key = f"{site_id or 'auto'}:{site_slug(req)}"
    cached = _STATS_CACHE.get(cache_key)
    if cached is not None:
        return cached

    params = {}
    if site_id is not None:
        params["site_id"] = site_id

    try:
        resp = await api_get(req, "/statistics/", params=params or None, soft=True)
        row = _extract_row(resp)
        projected = _project(row)
    except Exception:
        projected = _project({})

    _STATS_CACHE.set(cache_key, projected)
    return projected


def site_slug(req: Request) -> str:
    site = getattr(getattr(req, "state", None), "site", None)
    slug = getattr(site, "slug", None)
    return slug or ""
