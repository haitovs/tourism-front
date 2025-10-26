# app/services/speakers.py
from __future__ import annotations

from typing import Optional

from fastapi import Request

from app.core.http import abs_media, api_get


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


async def get_featured_speakers(req: Request, *, limit: int = 3) -> list[dict]:
    import asyncio
    import logging

    import httpx
    log = logging.getLogger("services.speakers")

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
    return [_row_to_dict(r) for r in items[:max(1, int(limit))]]


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
    return [_row_to_dict(r) for r in items]


async def get_speaker(req: Request, *, speaker_id: int) -> Optional[dict]:
    import asyncio
    import logging

    import httpx
    log = logging.getLogger("services.speakers")

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

    return _row_to_dict(row) if row else None


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
    return ([_row_to_dict(r) for r in page_items], total_pages, total_items)
