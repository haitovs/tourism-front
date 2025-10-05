# app/services/expo_sectors.py
from contextlib import contextmanager
from typing import Generator, Optional
from urllib.parse import urljoin

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.settings import settings
from app.models.expo_sector_model import ExpoSector


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


def _resolve_logo_url(logo: str | None) -> str:
    if not logo:
        return "/static/img/default_sector.png"
    if logo.lower().startswith(("http://", "https://")):
        return logo
    base = settings.MEDIA_BASE_URL.rstrip("/") + "/"
    return urljoin(base, logo.lstrip("/"))


def list_all_sectors(site_id: Optional[int] = None) -> list[dict]:
    with _db_session() as db:
        stmt = select(ExpoSector)
        if site_id:
            stmt = stmt.where(ExpoSector.site_id == site_id)
        stmt = stmt.order_by(ExpoSector.id.asc())
        rows = db.execute(stmt).scalars().all()
        return [{
            "id": r.id,
            "header": r.header,
            "description": r.description,
            "logo_url": _resolve_logo_url(r.logo),
        } for r in rows]
