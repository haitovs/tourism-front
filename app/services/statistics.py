# app/services/statistics.py
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.statistics_model import Statistics


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


def get_statistics(site_id: Optional[int] = None) -> dict:
    """
    Always return a dict with 4 integer keys.
    """
    defaults = {
        "episodes": 0,
        "delegates": 0,
        "speakers": 0,
        "companies": 0,
    }

    with _db_session() as db:
        stmt = select(Statistics)
        if site_id:
            stmt = stmt.where(Statistics.site_id == site_id)

        row = db.execute(stmt).scalars().first()
        if not row:
            return defaults

        return {
            "episodes": int(getattr(row, "episodes", 0) or 0),
            "delegates": int(getattr(row, "delegates", 0) or 0),
            "speakers": int(getattr(row, "speakers", 0) or 0),
            "companies": int(getattr(row, "companies", 0) or 0),
        }
