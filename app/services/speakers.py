# app/services/speakers.py
from __future__ import annotations

from typing import Optional

from fastapi import Request

from app.core.http import abs_media, api_get
from app.utils.timed_cache import TimedCache


def _resolve_media(path: str | None) -> str:
    return abs_media(path)


def _display_full_name(first: str, surname: str, full_name_db: str) -> str:
    if full_name_db:
        return full_name_db
    parts = [p for p in [first, surname] if p]
    return " ".join(parts)


def _row_to_dict(row: dict) -> dict:
    first = (row.get("name") or "").strip()
    surname = (row.get("surname") or "").strip()
    full_name_db = (row.get("full_name") or "").strip()

    return {
        "id": row.get("id"),
        "fullname": _display_full_name(first, surname, full_name_db),
        "name": first,
        "surname": surname,
        "company": row.get("company") or "",
        "position": row.get("position") or "",
        "description": row.get("description") or "",
        "photo_url": _resolve_media(row.get("photo")),
        "company_photo_url": _resolve_media(row.get("company_photo")),
        "website": row.get("website") or "",
        "email": row.get("email") or "",
        "phone": row.get("phone") or "",
        "links": row.get("social_links") or [],
        "sessions": row.get("sessions") or [],
    }


_FEATURED_CACHE = TimedCache(ttl_seconds=20.0)
_LIST_CACHE = TimedCache(ttl_seconds=20.0)
_PAGE_CACHE = TimedCache(ttl_seconds=20.0)
_DETAIL_CACHE = TimedCache(ttl_seconds=30.0)


def _site_cache_key(req: Request) -> str:
    site = getattr(getattr(req, "state", None), "site", None)
    sid = getattr(site, "id", None) or 0
    slug = getattr(site, "slug", None) or ""
    lang = getattr(getattr(req, "state", None), "lang", "") or ""
    return f"{sid}:{slug}:{lang}"


async def get_featured_speakers(req: Request, *, limit: int = 3) -> list[dict]:
    import asyncio
    import logging

    import httpx
    log = logging.getLogger("services.speakers")

    cache_key = f"featured:{_site_cache_key(req)}:{limit}"
    cached = _FEATURED_CACHE.get(cache_key)
    if cached is not None:
        return cached

    items = None
    for attempt in range(2):  # 1 try + 1 retry
        try:
            items = await api_get(req, "/speakers/")
            break
        except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
            log.warning("get_featured_speakers timeout (attempt %d/2): %s", attempt + 1, e)
            if attempt == 0:
                await asyncio.sleep(0.35)
                continue
        except httpx.HTTPError as e:
            log.error("get_featured_speakers HTTP error: %r", e)
            break
        except Exception as e:
            log.exception("get_featured_speakers unexpected: %r", e)
            break

    items = items or []
    items.sort(key=lambda x: x.get("id") or 0, reverse=True)  # newest first by id
    projected = [_row_to_dict(r) for r in items[:max(1, int(limit))]]
    _FEATURED_CACHE.set(cache_key, projected)
    return projected


async def list_speakers(
    req: Request,
    *,
    limit: Optional[int] = None,
    latest_first: bool = True,
) -> list[dict]:
    import asyncio
    import logging

    import httpx
    log = logging.getLogger("services.speakers")

    cache_key = f"list:{_site_cache_key(req)}:{limit}:{latest_first}"
    cached = _LIST_CACHE.get(cache_key)
    if cached is not None:
        return cached

    items = None
    for attempt in range(2):
        try:
            items = await api_get(req, "/speakers/")
            break
        except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
            log.warning("list_speakers timeout (attempt %d/2): %s", attempt + 1, e)
            if attempt == 0:
                await asyncio.sleep(0.35)
                continue
        except httpx.HTTPError as e:
            log.error("list_speakers HTTP error: %r", e)
            break
        except Exception as e:
            log.exception("list_speakers unexpected: %r", e)
            break

    items = items or []
    items.sort(key=lambda x: x.get("id") or 0, reverse=latest_first)
    if limit:
        items = items[:max(1, int(limit))]
    projected = [_row_to_dict(r) for r in items]
    _LIST_CACHE.set(cache_key, projected)
    return projected


async def get_speaker(req: Request, *, speaker_id: int) -> Optional[dict]:
    import asyncio
    import logging

    import httpx
    log = logging.getLogger("services.speakers")

    cache_key = f"detail:{_site_cache_key(req)}:{speaker_id}"
    cached = _DETAIL_CACHE.get(cache_key)
    if cached is not None:
        return cached

    row = None
    for attempt in range(2):
        try:
            row = await api_get(req, f"/speakers/{speaker_id}")
            break
        except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
            log.warning("get_speaker[%s] timeout (attempt %d/2): %s", speaker_id, attempt + 1, e)
            if attempt == 0:
                await asyncio.sleep(0.35)
                continue
        except httpx.HTTPError as e:
            log.error("get_speaker[%s] HTTP error: %r", speaker_id, e)
            return None
        except Exception as e:
            log.exception("get_speaker[%s] unexpected: %r", speaker_id, e)
            return None

    if not row:
        return None
    projected = _row_to_dict(row)
    _DETAIL_CACHE.set(cache_key, projected)
    return projected


async def list_speakers_page(
    req: Request,
    *,
    page: int = 1,
    per_page: int = 9,
    latest_first: bool = True,
) -> tuple[list[dict], int, int]:
    import asyncio
    import logging

    import httpx
    log = logging.getLogger("services.speakers")

    page = max(1, int(page))
    per_page = max(1, int(per_page))

    cache_key = f"page:{_site_cache_key(req)}:{page}:{per_page}:{latest_first}"
    cached = _PAGE_CACHE.get(cache_key)
    if cached is not None:
        return cached

    items = None
    for attempt in range(2):
        try:
            items = await api_get(req, "/speakers/")
            break
        except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
            log.warning("list_speakers_page timeout (attempt %d/2): %s", attempt + 1, e)
            if attempt == 0:
                await asyncio.sleep(0.35)
                continue
        except httpx.HTTPError as e:
            log.error("list_speakers_page HTTP error: %r", e)
            break
        except Exception as e:
            log.exception("list_speakers_page unexpected: %r", e)
            break

    items = items or []
    items.sort(key=lambda x: x.get("id") or 0, reverse=latest_first)

    total_items = len(items)
    total_pages = max(1, (total_items + per_page - 1) // per_page)
    start = (page - 1) * per_page
    end = start + per_page
    page_items = items[start:end]
    projected = [_row_to_dict(r) for r in page_items]
    payload = (projected, total_pages, total_items)
    _PAGE_CACHE.set(cache_key, payload)
    return payload
