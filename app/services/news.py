# app/services/news.py
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from typing import Generator, Optional
from urllib.parse import urljoin

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.settings import settings
from app.models.news_model import News


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


def get_latest_news(*, limit: int = 5, site_id: Optional[int] = None) -> list[dict]:
    """
    Latest published news by created_at desc (fallback id desc).
    Exposes only what the template needs.
    """
    out: list[dict] = []
    with _db_session() as db:
        stmt = select(News).where(News.is_published.is_(True))
        if site_id is not None:
            stmt = stmt.where(News.site_id == site_id)

        # order newest first
        if hasattr(News, "created_at"):
            stmt = stmt.order_by(desc(News.created_at), desc(News.id))
        else:
            stmt = stmt.order_by(desc(News.id))

        rows = db.execute(stmt.limit(max(1, limit))).scalars().all()

        for r in rows:
            dt: Optional[datetime] = getattr(r, "created_at", None)
            out.append({
                "id": r.id,
                "title": getattr(r, "header", "") or "",
                "summary": getattr(r, "description", "") or "",
                "category": getattr(r, "category", "") or "News",
                "image_url": _resolve_media(getattr(r, "photo", None)),
                "date_iso": dt.isoformat() if dt else None,
                "date_human": dt.strftime("%d %b %y") if dt else "",
            })
    return out


def get_news(news_id: int, site_id: Optional[int] = None) -> Optional[dict]:
    with _db_session() as db:
        stmt = select(News).where(News.id == news_id, News.is_published.is_(True))
        if site_id is not None:
            stmt = stmt.where(News.site_id == site_id)
        r = db.execute(stmt).scalars().first()
        if not r:
            return None
        dt = getattr(r, "created_at", None)
        return {
            "id": r.id,
            "title": getattr(r, "header", "") or "",
            "summary": getattr(r, "description", "") or "",
            "body": getattr(r, "body", None) or "",
            "category": getattr(r, "category", "") or "News",
            "image_url": _resolve_media(getattr(r, "photo", None)),
            "date_iso": dt.isoformat() if dt else None,
            "date_human": dt.strftime("%d %b %y") if dt else "",
        }
