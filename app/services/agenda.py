# app/services/agenda.py
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Optional
from urllib.parse import urljoin

from sqlalchemy import and_, select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.sql import nulls_last

from app.core.db import get_db
from app.core.settings import settings
from app.models.agenda_model import AgendaDay
from app.models.episode_model import Episode


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
    """Return absolute URL for media path using MEDIA_BASE_URL / MEDIA_PREFIX."""
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


# ---------- Row → DTO mappers ----------


def _episode_to_dict(ep: Episode) -> dict:
    # Speakers
    speakers = []
    for s in (getattr(ep, "speakers", None) or []):
        speakers.append({
            "id": s.id,
            "fullname": (getattr(s, "full_name", None) or " ".join([
                (getattr(s, "name", "") or "").strip(),
                (getattr(s, "surname", "") or "").strip(),
            ]).strip()) or "",
            "position": getattr(s, "position", "") or "",
            "company": getattr(s, "company", "") or "",
            "photo_url": _resolve_media(getattr(s, "photo", None)),
        })

    # Moderators (front model may not have surname/position/company; defaults OK)
    moderators = []
    for m in (getattr(ep, "moderators", None) or []):
        moderators.append({
            "id":
                m.id,
            "fullname": (getattr(m, "full_name", None) or " ".join([
                (getattr(m, "name", "") or "").strip(),
                (getattr(m, "surname", "") or "").strip(),
            ]).strip()) or (getattr(m, "name", "") or ""),
            "position":
                getattr(m, "position", "") or "",
            "company":
                getattr(m, "company", "") or "",
            "description":
                getattr(m, "description", "") or "",
            "photo_url":
                _resolve_media(getattr(m, "photo", None)),
        })

    # Sponsors
    sponsors = []
    for sp in (getattr(ep, "sponsors", None) or []):
        sponsors.append({
            "id": sp.id,
            "name": getattr(sp, "name", "") or "",
            "logo_url": _resolve_media(getattr(sp, "logo", None)),
            "tier": getattr(sp, "tier", "") or "",
        })

    return {
        "id": ep.id,
        "slug": getattr(ep, "slug", "") or "",
        "title": ep.title,
        "description_md": getattr(ep, "description_md", "") or "",
        "start_time": ep.start_time,
        "end_time": ep.end_time,
        "location": getattr(ep, "location", "") or "",
        "published": bool(getattr(ep, "published", True)),
        "sort_order": getattr(ep, "sort_order", None),
        "hero_image_url": _resolve_media(getattr(ep, "hero_image_url", None)),
        "speakers": speakers,
        "moderators": moderators,
        "sponsors": sponsors,
        "day_id": ep.day_id,
        "site_id": ep.site_id,
    }


def _day_to_dict(d: AgendaDay) -> dict:
    return {
        "id": d.id,
        "date": d.date,
        "label": getattr(d, "label", "") or "",
        "published": bool(getattr(d, "published", True)),
        "sort_order": getattr(d, "sort_order", None),
        "site_id": d.site_id,
    }


# ---------- Queries ----------


def list_days(*, site_id: Optional[int] = None, only_published: bool = True) -> list[dict]:
    with _db_session() as db:
        stmt = select(AgendaDay)
        if site_id is not None:
            stmt = stmt.where(AgendaDay.site_id == site_id)
        if only_published:
            stmt = stmt.where(AgendaDay.published.is_(True))

        stmt = stmt.order_by(
            nulls_last(AgendaDay.sort_order.asc()),  # ASC NULLS LAST
            AgendaDay.date.asc(),
            AgendaDay.id.asc(),
        )

        rows = db.execute(stmt).scalars().all()
        return [_day_to_dict(r) for r in rows]


def list_episodes_for_day(
    *,
    day_id: int,
    site_id: int | None = None,
    only_published: bool = True,
) -> list[dict]:
    with _db_session() as db:
        conds = [Episode.day_id == day_id]
        if site_id is not None:
            conds.append(Episode.site_id == site_id)
        if only_published:
            conds.append(Episode.published.is_(True))

        stmt = (select(Episode).options(
            selectinload(Episode.speakers),
            selectinload(Episode.moderators),
            selectinload(Episode.sponsors),
        ).where(and_(*conds)).order_by(
            nulls_last(Episode.sort_order.asc()),
            Episode.start_time.asc(),
            Episode.id.asc(),
        ))

        episodes = db.execute(stmt).scalars().all()  # selectinload ⇒ no .unique() needed
        return [_episode_to_dict(ep) for ep in episodes]


def list_days_with_episodes(
    *,
    site_id: Optional[int] = None,
    only_published: bool = True,
) -> list[dict]:
    """Return days with an `episodes` list each."""
    days = list_days(site_id=site_id, only_published=only_published)
    out: list[dict] = []
    for d in days:
        eps = list_episodes_for_day(day_id=d["id"], site_id=site_id, only_published=only_published)
        out.append({**d, "episodes": eps})
    return out
