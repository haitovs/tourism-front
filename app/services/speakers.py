# app/services/speakers.py
from __future__ import annotations

from typing import List, Optional, Tuple

from fastapi import Request

from app.core.http import abs_media, api_get
from app.core.settings import settings


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
    items = await api_get(req, "/speakers/") or []
    # newest first by id
    items.sort(key=lambda x: x.get("id") or 0, reverse=True)
    return [_row_to_dict(r) for r in items[:max(1, int(limit))]]


async def list_speakers(
    req: Request,
    *,
    limit: Optional[int] = None,
    latest_first: bool = True,
) -> list[dict]:
    items = await api_get(req, "/speakers/") or []
    items.sort(key=lambda x: x.get("id") or 0, reverse=latest_first)
    if limit:
        items = items[:max(1, int(limit))]
    return [_row_to_dict(r) for r in items]


async def get_speaker(req: Request, *, speaker_id: int) -> Optional[dict]:
    row = await api_get(req, f"/speakers/{speaker_id}")
    return _row_to_dict(row) if row else None


async def list_speakers_page(
    req: Request,
    *,
    page: int = 1,
    per_page: int = 9,
    latest_first: bool = True,
) -> tuple[list[dict], int, int]:
    page = max(1, int(page))
    per_page = max(1, int(per_page))
    items = await api_get(req, "/speakers/") or []
    items.sort(key=lambda x: x.get("id") or 0, reverse=latest_first)

    total_items = len(items)
    total_pages = max(1, (total_items + per_page - 1) // per_page)
    start = (page - 1) * per_page
    end = start + per_page
    page_items = items[start:end]
    return ([_row_to_dict(r) for r in page_items], total_pages, total_items)
