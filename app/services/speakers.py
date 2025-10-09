# app/services/speakers.py
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Optional
from urllib.parse import urljoin

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.settings import settings
from app.models.speaker_model import Speaker


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
    return urljoin(base, f"{pref}/{path.lstrip('/')}")  # <-- the line that was cut off before


def _row_to_dict(r: Speaker) -> dict:
    return {
        "id": r.id,
        "name": getattr(r, "full_name", "") or getattr(r, "name", ""),
        "position": getattr(r, "position", "") or "",
        "photo_url": _resolve_media(getattr(r, "photo", None)),
    }


def get_featured_speakers(*, limit: int = 3, site_id: Optional[int] = None) -> list[dict]:
    """
    Latest-added speakers (by id desc), limited to `limit`.
    """
    out: list[dict] = []
    with _db_session() as db:
        stmt = select(Speaker)
        if site_id is not None:
            stmt = stmt.where(Speaker.site_id == site_id)
        stmt = stmt.order_by(desc(Speaker.id)).limit(max(1, limit))
        rows = db.execute(stmt).scalars().all()
        for r in rows:
            out.append(_row_to_dict(r))
    return out


def list_speakers(
    *,
    site_id: Optional[int] = None,
    limit: Optional[int] = None,
    latest_first: bool = True,
) -> list[dict]:
    """
    Full speaker listing (optionally limited). Ordered by id.
    """
    out: list[dict] = []
    with _db_session() as db:
        stmt = select(Speaker)
        if site_id is not None:
            stmt = stmt.where(Speaker.site_id == site_id)
        stmt = stmt.order_by(desc(Speaker.id) if latest_first else Speaker.id.asc())
        if limit:
            stmt = stmt.limit(max(1, limit))
        rows = db.execute(stmt).scalars().all()
        for r in rows:
            out.append(_row_to_dict(r))
    return out


def get_speaker(*, speaker_id: int, site_id: Optional[int] = None) -> Optional[dict]:
    """
    Fetch a single speaker by id. Returns None if not found.
    """
    with _db_session() as db:
        stmt = select(Speaker).where(Speaker.id == speaker_id)
        if site_id is not None:
            stmt = stmt.where(Speaker.site_id == site_id)
        r = db.execute(stmt).scalars().first()
        return _row_to_dict(r) if r else None
