# app/services/partners.py
from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import Request

from app.core.http import abs_media, api_get
from app.core.settings import settings
from app.utils.timed_cache import TimedCache


def _row_to_dict(row: dict) -> dict:
    return {
        "id": row.get("id"),
        "name": row.get("name") or "",
        "website": row.get("website") or "",
        "logo_url": abs_media(row.get("logo")),
        "type": row.get("type") or "",
    }


async def list_partners(
    req: Request,
    *,
    limit: Optional[int] = None,
    latest_first: bool = True,
) -> List[Dict]:
    import asyncio
    import logging

    import httpx

    log = logging.getLogger("services.partners")

    cache_key = f"partners:{_site_cache_key(req)}:{limit}:{latest_first}"
    cached = _LIST_CACHE.get(cache_key)
    if cached is not None:
        return cached

    rows = None
    for attempt in range(2):  # try once, then one retry
        try:
            rows = await api_get(req, "/partners/")
            break
        except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
            log.warning("partners: timeout (attempt %d/2): %s", attempt + 1, e)
            if attempt == 0:
                await asyncio.sleep(0.5)  # small backoff
                continue
        except httpx.HTTPError as e:
            log.error("partners: HTTP error: %r", e)
            break
        except Exception as e:
            log.exception("partners: unexpected error: %r", e)
            break

    rows = rows or []
    rows.sort(key=lambda x: x.get("id") or 0, reverse=latest_first)
    if limit:
        rows = rows[:max(1, int(limit))]
    projected = [_row_to_dict(r) for r in rows]
    _LIST_CACHE.set(cache_key, projected)
    return projected


async def as_carousel_data(req: Request, *, limit: Optional[int] = None) -> dict:
    return {
        "items": await list_partners(req, limit=limit),
        "label": "Partner",
        "kind": "partners",
    }
_LIST_CACHE = TimedCache(ttl_seconds=30.0)


def _site_cache_key(req: Request) -> str:
    site = getattr(getattr(req, "state", None), "site", None)
    sid = getattr(site, "id", None) or getattr(settings, "FRONT_SITE_ID", 0)
    slug = getattr(site, "slug", None) or getattr(settings, "FRONT_SITE_SLUG", "")
    return f"{sid}:{slug}"
