# app/services/partners.py
from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import Request

from app.core.http import abs_media, api_get
from app.core.settings import settings


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
    rows = await api_get(req, "/partners/") or []
    rows.sort(key=lambda x: x.get("id") or 0, reverse=latest_first)
    if limit:
        rows = rows[:max(1, int(limit))]
    return [_row_to_dict(r) for r in rows]


async def as_carousel_data(req: Request, *, limit: Optional[int] = None) -> dict:
    return {
        "items": await list_partners(req, limit=limit),
        "label": "Partner",
        "kind": "partners",
    }
