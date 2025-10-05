from __future__ import annotations
from typing import Literal, Optional, Generator
from contextlib import contextmanager

from sqlalchemy import select, asc
from sqlalchemy.orm import Session
from sqlalchemy.exc import DataError

from app.core.db import get_db
from app.models.sponsor_model import Sponsor, SponsorTier

TopTier = Literal["premier", "general", "diamond", "platinum"]
ListTier = Literal["gold", "silver", "bronze"]

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

def _project(sp: Sponsor) -> dict:
    if not sp:
        return {}
    return {
        "id": sp.id,
        "name": sp.name,
        "website": sp.website or "",
        "logo_url": sp.logo or "",
        "tier": sp.tier.value if isinstance(sp.tier, SponsorTier) else str(sp.tier),
    }

def get_top_sponsors(*, lang: str = "en", site_id: Optional[int] = None) -> dict[TopTier, list[dict]]:
    tiers: list[TopTier] = ["premier", "general", "diamond", "platinum"]
    out: dict[TopTier, list[dict]] = {t: [] for t in tiers}
    with _db_session() as db:
        for t in tiers:
            try:
                enum_val = SponsorTier(t)  # use Python enum to bind correctly
            except ValueError:
                # not a valid Python enum member; skip
                continue
            stmt = select(Sponsor).where(Sponsor.tier == enum_val)
            if site_id is not None:
                stmt = stmt.where(Sponsor.site_id == site_id)
            stmt = stmt.order_by(asc(Sponsor.id)).limit(1)
            try:
                row = db.execute(stmt).scalars().first()
            except DataError:
                # DB enum may be missing this value; skip gracefully
                row = None
            if row:
                out[t] = [_project(row)]
    return out

def list_sponsors_by_tier(
    *, tier: ListTier, page: int = 1, per_page: int = 4, lang: str = "en", site_id: Optional[int] = None
) -> dict:
    offset = (max(page, 1) - 1) * per_page
    try:
        enum_val = SponsorTier(tier)
    except ValueError:
        return {"items": [], "page": max(page, 1), "per_page": per_page, "tier": tier}
    with _db_session() as db:
        stmt = select(Sponsor).where(Sponsor.tier == enum_val)
        if site_id is not None:
            stmt = stmt.where(Sponsor.site_id == site_id)
        stmt = stmt.order_by(asc(Sponsor.id)).offset(offset).limit(per_page)
        try:
            items = db.execute(stmt).scalars().all()
        except DataError:
            # DB enum missing this value -> empty
            items = []
    return {"items": [_project(sp) for sp in items], "page": max(page, 1), "per_page": per_page, "tier": tier}
