# app/services/moderators.py
from __future__ import annotations

from typing import Optional

from fastapi import Request

from app.core.http import api_get
from app.core.settings import settings


def _resolve_media(path: str | None) -> str:
    """Turn a stored path into an absolute URL using MEDIA_BASE_URL / MEDIA_PREFIX."""
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
    """
    Normalize backend Moderator payload to the shape templates use.
    Backend fields: id, name, description, photo, ...
    """
    fullname = (row.get("name") or "").strip()
    return {
        "id": row.get("id"),
        "fullname": fullname,  # templates use .fullname
        "name": fullname,  # keep alias (harmless)
        "position": "",  # Moderator has no position/company
        "company": "",
        "description": row.get("description") or "",
        "photo_url": _resolve_media(row.get("photo")),
        # keep a consistent shape with speaker dicts
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
    """
    Fetch moderators from backend (already localized via middleware cookies/headers).
    Client-side order by id (desc/asc) and apply optional limit.
    """
    items = await api_get(req, "/moderators/") or []
    # sort by id
    items.sort(key=lambda x: x.get("id") or 0, reverse=latest_first)
    if limit:
        items = items[:max(1, int(limit))]
    return [_row_to_dict(it) for it in items]


async def get_moderator(
    req: Request,
    *,
    moderator_id: int,
) -> Optional[dict]:
    row = await api_get(req, f"/moderators/{moderator_id}")
    return _row_to_dict(row) if row else None


async def list_moderators_page(
    req: Request,
    *,
    page: int = 1,
    per_page: int = 12,
    latest_first: bool = True,
) -> tuple[list[dict], int, int]:
    """
    Simple client-side pagination: fetch all then slice.
    Returns (items, total_pages, total_items).
    """
    page = max(1, int(page))
    per_page = max(1, int(per_page))

    items = await api_get(req, "/moderators/") or []
    items.sort(key=lambda x: x.get("id") or 0, reverse=latest_first)

    total_items = len(items)
    total_pages = max(1, (total_items + per_page - 1) // per_page)

    start = (page - 1) * per_page
    end = start + per_page
    page_items = items[start:end]

    return ([_row_to_dict(it) for it in page_items], total_pages, total_items)
