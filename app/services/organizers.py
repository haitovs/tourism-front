# app/services/organizers.py
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Optional
from urllib.parse import urljoin

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.settings import settings
from app.models.organizer_model import Organizer


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
    Resolve DB-stored relative/absolute paths to a usable URL, identical to speakers.py behavior:
    - If path is http(s) -> return as-is
    - Else: urljoin(MEDIA_BASE_URL, <MEDIA_PREFIX>/<path>)
    - Handles leading slashes gracefully
    """
    if not path:
        return ""
    low = path.lower()
    if low.startswith("http://") or low.startswith("https://"):
        return path

    base = settings.MEDIA_BASE_URL.rstrip("/") + "/"
    if path.startswith("/"):
        # Treat as app-absolute path; strip leading slash then join
        return urljoin(base, path.lstrip("/"))

    pref = settings.MEDIA_PREFIX.strip("/")
    return urljoin(base, f"{pref}/{path.lstrip('/')}")


def list_organizers(
    *,
    site_id: Optional[int] = None,
    latest_first: bool = True,
    limit: Optional[int] = None,
) -> list[dict]:
    """
    Return organizers as view-ready dicts.
    By default returns ALL (no limit) to feed a scrollable carousel.
    Order: newest first (id DESC) unless latest_first=False.
    """
    out: list[dict] = []
    with _db_session() as db:
        stmt = select(Organizer)
        if site_id is not None:
            stmt = stmt.where(Organizer.site_id == site_id)

        stmt = stmt.order_by(desc(Organizer.id) if latest_first else Organizer.id.asc())

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
    Convenience payload for the carousel partial.
    Shape matches your existing pattern used by sponsors.
    """
    return {
        "items": list_organizers(site_id=site_id),
        "label": "Organizer",
        "kind": "organizers",
    }
