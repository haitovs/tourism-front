# app/services/organizers.py
from __future__ import annotations

from typing import Optional

from fastapi import Request

from app.core.http import abs_media, api_get
from app.core.settings import settings


def _resolve_media(path: str | None) -> str:
    return abs_media(path)


def _row_to_dict(row: dict) -> dict:
    return {
        "id": row.get("id"),
        "name": row.get("name") or "",
        "website": row.get("website") or "",
        "logo_url": _resolve_media(row.get("logo")),
    }


async def list_organizers(
    req: Request,
    *,
    limit: Optional[int] = None,
) -> list[dict]:
    import asyncio
    import logging

    import httpx

    log = logging.getLogger("services.organizers")

    rows = None
    for attempt in range(2):
        try:
            rows = await api_get(req, "/organizers/")
            break
        except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
            log.warning("organizers: timeout (attempt %d/2): %s", attempt + 1, e)
            if attempt == 0:
                await asyncio.sleep(0.5)
                continue
        except httpx.HTTPError as e:
            log.error("organizers: HTTP error: %r", e)
            break
        except Exception as e:
            log.exception("organizers: unexpected error: %r", e)
            break

    items = [_row_to_dict(r) for r in (rows or [])]
    if limit is not None:
        items = items[:max(1, int(limit))]
    return items


async def as_carousel_data(
    req: Request,
    *,
    limit: Optional[int] = None,
) -> dict:
    return {
        "items": await list_organizers(req, limit=limit),
        "label": "Organizer",
        "kind": "organizers",
    }
