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
    import logging
    log = logging.getLogger("services.statistics")

    defaults = {
        "episodes": 0,
        "delegates": 0,
        "speakers": 0,
        "companies": 0,
    }

    try:
        with _db_session() as db:
            stmt = select(Statistics)
            if site_id is not None:
                stmt = stmt.where(Statistics.site_id == site_id)

            row = db.execute(stmt).scalars().first()
            if not row:
                return defaults

            def _to_int(v):
                try:
                    return int(v or 0)
                except Exception:
                    return 0

            return {
                "episodes": _to_int(getattr(row, "episodes", 0)),
                "delegates": _to_int(getattr(row, "delegates", 0)),
                "speakers": _to_int(getattr(row, "speakers", 0)),
                "companies": _to_int(getattr(row, "companies", 0)),
            }
    except Exception as e:
        log.exception("get_statistics unexpected: %r", e)
        return defaults
