# app/services/partners.py
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Optional
from urllib.parse import urljoin

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.settings import settings
from app.models.partner_model import Partner  # file you already have


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
    """
    Align with speakers.py:
    - http(s) -> as-is
    - else join: MEDIA_BASE_URL + MEDIA_PREFIX + path
    """
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


def list_partners(*, site_id: Optional[int] = None, limit: int | None = None) -> list[dict]:
    """
    Return partners as simple view dicts.
    Order: newest first (id DESC). No default limit (fits a carousel).
    """
    out: list[dict] = []
    with _db_session() as db:
        stmt = select(Partner)
        if site_id is not None:
            stmt = stmt.where(Partner.site_id == site_id)
        stmt = stmt.order_by(desc(Partner.id))
        if limit:
            stmt = stmt.limit(max(1, limit))

        rows = db.execute(stmt).scalars().all()
        for r in rows:
            out.append({
                "id": r.id,
                "name": r.name,
                "website": r.website or "",
                "logo_url": _resolve_media(getattr(r, "logo", None)),
            })
    return out


def as_carousel_data(*, site_id: Optional[int] = None) -> dict:
    """
    Optional helper if you want a dedicated partners carousel include.
    """
    return {
        "items": list_partners(site_id=site_id),
        "kind": "partners",
    }
