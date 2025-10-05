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
    with _db_session() as db:
        stmt = select(Statistics)
        if site_id:
            stmt = stmt.where(Statistics.site_id == site_id)
        row = db.execute(stmt).scalars().first()
        if not row:
            return None
        return {
            "episodes": row.episodes,
            "delegates": row.delegates,
            "speakers": row.speakers,
            "companies": row.companies,
        }
