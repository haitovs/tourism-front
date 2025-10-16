# app/services/moderators.py
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Optional
from urllib.parse import urljoin

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.settings import settings
from app.models.moderator_model import Moderator


# --- session helper (same pattern as speakers_srv) ---
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


# --- media resolver (same as speakers_srv) ---
def _resolve_media(path: str | None) -> str:
    if not path:
        return ""
    low = path.lower()
    if low.startswith("http://") or low.startswith("https://"):
        return path
    base = settings.MEDIA_BASE_URL.rstrip("/") + "/"
    if path.startswith("/"):
        return urljoin(base, path.lstrip("/"))
    pref = settings.MEDIA_PREFIX.strip("/")
    return urljoin(base, f"{pref}/{path.lstrip('/')}")


# --- row → dict (fields aligned to what templates expect) ---
def _row_to_dict(r: Moderator) -> dict:
    fullname = (getattr(r, "name", "") or "").strip()
    return {
        "id": r.id,
        "fullname": fullname,  # templates use .fullname
        "name": fullname,
        "position": "",  # Moderator model has no position/company
        "company": "",
        "description": getattr(r, "description", "") or "",
        "photo_url": _resolve_media(getattr(r, "photo", None)),
        # keep a consistent shape with speaker dicts
        "website": "",
        "email": "",
        "phone": "",
        "links": [],
    }


# --- public API ---


def list_moderators(
    *,
    site_id: Optional[int] = None,
    limit: Optional[int] = None,
    latest_first: bool = True,
) -> list[dict]:
    with _db_session() as db:
        stmt = select(Moderator)
        if site_id is not None:
            stmt = stmt.where(Moderator.site_id == site_id)
        stmt = stmt.order_by(desc(Moderator.id) if latest_first else Moderator.id.asc())
        if limit:
            stmt = stmt.limit(max(1, limit))
        rows = db.execute(stmt).scalars().all()
        return [_row_to_dict(r) for r in rows]


def get_moderator(*, moderator_id: int, site_id: Optional[int] = None) -> Optional[dict]:
    with _db_session() as db:
        stmt = select(Moderator).where(Moderator.id == moderator_id)
        if site_id is not None:
            stmt = stmt.where(Moderator.site_id == site_id)
        r = db.execute(stmt).scalars().first()
        return _row_to_dict(r) if r else None


def list_moderators_page(
    *,
    site_id: Optional[int] = None,
    page: int = 1,
    per_page: int = 12,
    latest_first: bool = True,
) -> tuple[list[dict], int, int]:
    page = max(1, page)
    per_page = max(1, per_page)
    with _db_session() as db:
        base = select(Moderator)
        if site_id is not None:
            base = base.where(Moderator.site_id == site_id)

        total_items = db.execute(select(func.count()).select_from(base.subquery())).scalar_one()

        stmt = base.order_by(desc(Moderator.id) if latest_first else Moderator.id.asc()) \
                   .offset((page - 1) * per_page).limit(per_page)

        rows = db.execute(stmt).scalars().all()
        items = [_row_to_dict(r) for r in rows]

        total_pages = max(1, (total_items + per_page - 1) // per_page)
        return items, total_pages, total_items
