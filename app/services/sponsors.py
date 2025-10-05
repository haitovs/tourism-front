from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Literal, Optional
from urllib.parse import urljoin

from sqlalchemy import asc, select
from sqlalchemy.exc import DataError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.settings import settings
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


def _resolve_logo_url(logo: str | None) -> str:
    """
    Build a publicly accessible URL for the sponsor logo.
    - If logo is absolute (http/https), return as-is.
    - If logo starts with '/', prefix with MEDIA_BASE_URL.
    - Else, prefix with MEDIA_BASE_URL + '/' + MEDIA_PREFIX + '/' + logo.
    """
    if not logo:
        return ""

    # Absolute URL -> leave unchanged
    low = logo.lower()
    if low.startswith("http://") or low.startswith("https://"):
        return logo

    base = settings.MEDIA_BASE_URL.rstrip("/") + "/"

    if logo.startswith("/"):
        # root-relative path from backend (e.g. /uploads/...)
        return urljoin(base, logo.lstrip("/"))

    # bare relative (e.g. sponsors/abc.png)
    pref = settings.MEDIA_PREFIX.strip("/")
    path = f"{pref}/{logo.lstrip('/')}"
    return urljoin(base, path)


def _project(sp: Sponsor) -> dict:
    if not sp:
        return {}
    return {
        "id": sp.id,
        "name": sp.name,
        "website": sp.website or "",
        "logo_url": _resolve_logo_url(sp.logo),
        "tier": sp.tier.value if isinstance(sp.tier, SponsorTier) else str(sp.tier),
    }


def get_top_sponsors(*, lang: str = "en", site_id: Optional[int] = None) -> dict[TopTier, list[dict]]:
    tiers: list[TopTier] = ["premier", "general", "diamond", "platinum"]
    out: dict[TopTier, list[dict]] = {t: [] for t in tiers}
    with _db_session() as db:
        for t in tiers:
            try:
                enum_val = SponsorTier(t)
            except ValueError:
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


def list_sponsors_by_tier(*, tier: ListTier, page: int = 1, per_page: int = 10, lang: str = "en", site_id: Optional[int] = None) -> dict:
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
            items = []
    return {"items": [_project(sp) for sp in items], "page": max(page, 1), "per_page": per_page, "tier": tier}
