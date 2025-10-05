# app/services/statistics.py
from __future__ import annotations

from typing import TypedDict

import httpx

from app.core.settings import settings


class StatsOut(TypedDict, total=False):
    episodes: int
    delegates: int
    speakers: int
    companies: int


async def get_statistics() -> StatsOut | None:
    url = f"{settings.BACKEND_BASE_URL.rstrip('/')}/statistics"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(url)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            data = r.json() or {}
            return {
                "episodes": int(data.get("episodes", 0)),
                "delegates": int(data.get("delegates", 0)),
                "speakers": int(data.get("speakers", 0)),
                "companies": int(data.get("companies", 0)),
            }
    except Exception:
        return None
