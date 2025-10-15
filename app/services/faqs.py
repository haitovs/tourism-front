# app/services/faq.py
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.faq_model import FAQ


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


def list_faqs(*, site_id: Optional[int] = None, limit: int | None = None) -> list[dict]:
    """
    Return published FAQs ordered by sort_order (asc, NULLS LAST) then id desc.
    """
    out: list[dict] = []
    with _db_session() as db:
        stmt = select(FAQ).where(FAQ.published.is_(True))
        if site_id is not None:
            stmt = stmt.where(FAQ.site_id == site_id)

        sort_col = FAQ.sort_order
        stmt = stmt.order_by(sort_col.is_(None), sort_col.asc(), desc(FAQ.id))

        if limit:
            stmt = stmt.limit(max(1, limit))

        rows = db.execute(stmt).scalars().all()
        for r in rows:
            out.append({
                "id": r.id,
                "question": r.question,
                "answer_md": r.answer_md,
            })
    return out
