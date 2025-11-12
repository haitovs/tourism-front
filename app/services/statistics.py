# app/services/statistics.py
from __future__ import annotations

import asyncio
from contextlib import contextmanager
from functools import partial
from typing import Generator, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.statistics_model import Statistics
from app.utils.timed_cache import TimedCache

_STATS_CACHE = TimedCache(ttl_seconds=30.0)


@contextmanager
def _db_session() -> Generator[Session, None, None]:
    gen = get_db()
    db = next(gen)
    try:
        yield db
    finally:
        try:
            gen.close()
        except Exception:
            pass


async def _run_in_thread(fn, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(fn, *args, **kwargs))


def _fetch_stats_sync(site_id: Optional[int]) -> dict:
    defaults = {
        "episodes": 0,
        "delegates": 0,
        "speakers": 0,
        "companies": 0,
    }
    with _db_session() as db:
        stmt = select(Statistics)
        if site_id is not None:
            stmt = stmt.where(Statistics.site_id == site_id)
        row = db.execute(stmt).scalars().first()
        if not row:
            return defaults

        def _to_int(val):
            try:
                return int(val or 0)
            except Exception:
                return 0

        return {
            "episodes": _to_int(getattr(row, "episodes", 0)),
            "delegates": _to_int(getattr(row, "delegates", 0)),
            "speakers": _to_int(getattr(row, "speakers", 0)),
            "companies": _to_int(getattr(row, "companies", 0)),
        }


async def get_statistics(site_id: Optional[int] = None) -> dict:
    cache_key = f"{site_id or 'all'}"
    cached = _STATS_CACHE.get(cache_key)
    if cached is not None:
        return cached

    try:
        data = await _run_in_thread(_fetch_stats_sync, site_id)
    except Exception:
        # fall back quickly if the DB is unhappy
        data = {
            "episodes": 0,
            "delegates": 0,
            "speakers": 0,
            "companies": 0,
        }
    else:
        _STATS_CACHE.set(cache_key, data)
    return data
