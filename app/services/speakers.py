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
    return urljoin(base, f"{pref}/{path.lstrip('/')}")


def get_featured_speakers(*, limit: int = 3, site_id: Optional[int] = None) -> list[dict]:
    """
    Return latest-added speakers (by id desc), limited to `limit`.
    """
    out: list[dict] = []
    with _db_session() as db:
        stmt = select(Speaker)
        if site_id is not None:
            stmt = stmt.where(Speaker.site_id == site_id)
        stmt = stmt.order_by(desc(Speaker.id)).limit(max(1, limit))
        rows = db.execute(stmt).scalars().all()
        for r in rows:
            out.append({
                "id": r.id,
                "name": getattr(r, "full_name", "") or getattr(r, "name", ""),
                "position": getattr(r, "position", "") or "",
                "photo_url": _resolve_media(getattr(r, "photo", None)),
            })
    return out
