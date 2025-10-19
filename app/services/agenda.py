# app/services/agenda.py
from __future__ import annotations

from contextlib import contextmanager
from typing import Dict, Generator, Iterable, List, Optional
from urllib.parse import urljoin

from sqlalchemy import and_, select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.sql import nulls_last

from app.core.db import get_db
from app.core.settings import settings
from app.models.agenda_model import AgendaDay
from app.models.episode_model import Episode

MEDIA_BASE = (settings.MEDIA_BASE_URL or "").rstrip("/")
MEDIA_PREFIX = (settings.MEDIA_PREFIX or "").strip("/")


@contextmanager
def _db_session() -> Generator[Session, None, None]:
    gen = get_db()
    db = next(gen)  # get the Session
    try:
        yield db
    finally:
        try:
            gen.close()
        except Exception:
            pass


def _resolve_media(path: Optional[str]) -> str:
    """
    Return absolute URL for media path using MEDIA_BASE_URL / MEDIA_PREFIX.
    - Passes through http(s)://
    - Handles leading/trailing slashes sanely
    """
    if not path:
        return ""
    low = path.lower()
    if low.startswith("http://") or low.startswith("https://"):
        return path

    if not MEDIA_BASE:
        # best-effort fallback: return as-is so the caller can decide
        return path

    # absolute path provided -> join to base directly
    if path.startswith("/"):
        return urljoin(MEDIA_BASE + "/", path.lstrip("/"))

    # relative path -> apply configured prefix if any
    if MEDIA_PREFIX:
        return urljoin(MEDIA_BASE + "/", f"{MEDIA_PREFIX}/{path.lstrip('/')}")
    return urljoin(MEDIA_BASE + "/", path.lstrip("/"))


# ---------- Row → DTO mappers ----------


def _episode_to_dict(ep: Episode) -> dict:
    speakers: List[dict] = []
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

    moderators: List[dict] = []
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

    sponsors: List[dict] = []
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


def list_days(*, site_id: Optional[int] = None, only_published: bool = True) -> List[dict]:
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
) -> List[dict]:
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

        episodes = db.execute(stmt).scalars().all()
        return [_episode_to_dict(ep) for ep in episodes]


def list_days_with_episodes(
    *,
    site_id: Optional[int] = None,
    only_published: bool = True,
) -> List[dict]:
    """
    Original implementation (kept for compatibility).
    Note: Runs one query per day for episodes (OK for small counts).
    Prefer `list_days_with_episodes_bulk` for larger programs.
    """
    days = list_days(site_id=site_id, only_published=only_published)
    out: List[dict] = []
    for d in days:
        eps = list_episodes_for_day(day_id=d["id"], site_id=site_id, only_published=only_published)
        out.append({**d, "episodes": eps})
    return out


# ---------- Optional: bulk loader (no N+1) ----------


def _group_by(items: Iterable[Episode], key_fn) -> Dict[int, List[Episode]]:
    grouped: Dict[int, List[Episode]] = {}
    for it in items:
        k = key_fn(it)
        grouped.setdefault(k, []).append(it)
    return grouped


def list_days_with_episodes_bulk(
    *,
    site_id: Optional[int] = None,
    only_published: bool = True,
) -> List[dict]:
    """
    Loads all days, then ALL episodes for those days in a single query
    (with `selectinload` for relations), and groups them by day_id.
    Drop-in replacement for `list_days_with_episodes` if desired.
    """
    with _db_session() as db:
        # 1) Days
        day_rows = list_days(site_id=site_id, only_published=only_published)
        if not day_rows:
            return []

        day_ids = [d["id"] for d in day_rows]

        # 2) Episodes for all days in one go
        conds = [Episode.day_id.in_(day_ids)]
        if site_id is not None:
            conds.append(Episode.site_id == site_id)
        if only_published:
            conds.append(Episode.published.is_(True))

        ep_stmt = (select(Episode).options(
            selectinload(Episode.speakers),
            selectinload(Episode.moderators),
            selectinload(Episode.sponsors),
        ).where(and_(*conds)).order_by(
            nulls_last(Episode.sort_order.asc()),
            Episode.start_time.asc(),
            Episode.id.asc(),
        ))

        episodes = db.execute(ep_stmt).scalars().all()
        by_day = _group_by(episodes, key_fn=lambda e: e.day_id)

        # 3) Assemble DTOs in the same day order
        out: List[dict] = []
        for d in day_rows:
            eps = [_episode_to_dict(ep) for ep in by_day.get(d["id"], [])]
            out.append({**d, "episodes": eps})
        return out
