# app/services/partners.py
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.partner_model import \
    Partner  # ensure file name matches your project


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


def _logo_url(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    if path.startswith(("http://", "https://", "/")):
        return path
    # naive fallback to a common media prefix
    return f"/media/{path}"


def list_partners(*, site_id: Optional[int] = None, limit: int | None = None) -> list[dict]:
    """
    Returns organizers/partners as simple view dicts.
    Order: sort by id DESC (latest first). Add more ordering if needed.
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
                "website": r.website,
                "logo_url": _logo_url(r.logo),
            })
    return out
