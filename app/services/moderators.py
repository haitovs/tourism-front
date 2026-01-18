# app/services/moderators.py
from __future__ import annotations

from typing import Optional

from fastapi import Request

from app.core.http import api_get
from app.core.settings import settings


def _resolve_media(path: str | None) -> str:
    if not path:
        return ""
    low = path.lower()
    if low.startswith("http://") or low.startswith("https://"):
        return path
    base = settings.MEDIA_BASE_URL.rstrip("/")
    pref = settings.MEDIA_PREFIX.strip("/")
    if path.startswith("/"):
        return f"{base}/{path.lstrip('/')}"
    return f"{base}/{pref}/{path.lstrip('/')}" if pref else f"{base}/{path.lstrip('/')}"


def _row_to_dict(row: dict) -> dict:
    fullname = (row.get("name") or "").strip()
    return {
        "id": row.get("id"),
        "fullname": fullname,
        "name": fullname,
        "position": "",
        "company": "",
        "description": row.get("description") or "",
        "photo_url": _resolve_media(row.get("photo")),
        "website": "",
        "email": "",
        "phone": "",
        "links": [],
    }


async def list_moderators(
    req: Request,
    *,
    limit: Optional[int] = None,
    latest_first: bool = True,
) -> list[dict]:
    import asyncio
    import logging

    import httpx
    log = logging.getLogger("services.moderators")

    items = None
    for attempt in range(2):
        try:
            items = await api_get(req, "/moderators/")
            break
        except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
            log.warning("list_moderators timeout (attempt %d/2): %s", attempt + 1, e)
            if attempt == 0:
                await asyncio.sleep(0.35)
                continue
        except httpx.HTTPError as e:
            log.error("list_moderators HTTP error: %r", e)
            break
        except Exception as e:
            log.exception("list_moderators unexpected: %r", e)
            break

    items = items or []
    items.sort(key=lambda x: x.get("id") or 0, reverse=latest_first)
    if limit:
        items = items[:max(1, int(limit))]
    return [_row_to_dict(it) for it in items]


async def get_moderator(
    req: Request,
    *,
    moderator_id: int,
) -> Optional[dict]:
    import asyncio
    import logging

    import httpx
    log = logging.getLogger("services.moderators")

    row = None
    for attempt in range(2):
        try:
            row = await api_get(req, f"/moderators/{moderator_id}")
            break
        except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
            log.warning("get_moderator[%s] timeout (attempt %d/2): %s", moderator_id, attempt + 1, e)
            if attempt == 0:
                await asyncio.sleep(0.35)
                continue
        except httpx.HTTPError as e:
            log.error("get_moderator[%s] HTTP error: %r", moderator_id, e)
            return None
        except Exception as e:
            log.exception("get_moderator[%s] unexpected: %r", moderator_id, e)
            return None

    return _row_to_dict(row) if row else None


async def list_moderators_page(
    req: Request,
    *,
    page: int = 1,
    per_page: int = 12,
    latest_first: bool = True,
) -> tuple[list[dict], int, int]:
    import asyncio
    import logging

    import httpx
    log = logging.getLogger("services.moderators")

    page = max(1, int(page))
    per_page = max(1, int(per_page))

    items = None
    for attempt in range(2):
        try:
            items = await api_get(req, "/moderators/")
            break
        except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
            log.warning("list_moderators_page timeout (attempt %d/2): %s", attempt + 1, e)
            if attempt == 0:
                await asyncio.sleep(0.35)
                continue
        except httpx.HTTPError as e:
            log.error("list_moderators_page HTTP error: %r", e)
            break
        except Exception as e:
            log.exception("list_moderators_page unexpected: %r", e)
            break

    items = items or []
    items.sort(key=lambda x: x.get("id") or 0, reverse=latest_first)

    total_items = len(items)
    total_pages = max(1, (total_items + per_page - 1) // per_page)

    start = (page - 1) * per_page
    end = start + per_page
    page_items = items[start:end]

    return ([_row_to_dict(it) for it in page_items], total_pages, total_items)
