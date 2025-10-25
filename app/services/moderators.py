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
    items = await api_get(req, "/moderators/") or []
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
