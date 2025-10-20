# app/services/episodes.py
from __future__ import annotations

import re
# NOTE: we re-use get_db generator pattern used in app/services/agenda.py
from contextlib import contextmanager
from typing import Iterable, List, Optional
from urllib.parse import urljoin

from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.settings import settings
from app.models.agenda_model import AgendaDay
from app.models.episode_model import Episode


@contextmanager
def _db_session():
    gen = get_db()
    db = next(gen)
    try:
        yield db
    finally:
        try:
            gen.close()
        except Exception:
            pass


def _resolve_media(path: Optional[str]) -> str:
    if not path:
        return ""
    low = path.lower()
    if low.startswith("http://") or low.startswith("https://"):
        return path
    base = settings.MEDIA_BASE_URL.rstrip("/") + "/"
    if path.startswith("/"):
        return urljoin(base, path.lstrip("/"))
    pref = settings.MEDIA_PREFIX.strip("/")
    if pref:
        return urljoin(base, f"{pref}/{path.lstrip('/')}")
    return urljoin(base, path.lstrip("/"))


def _strip_md(text: str) -> str:
    """Very small markdown stripper for short preview generation."""
    if not text:
        return ""
    s = text
    # remove code blocks / inline code
    s = re.sub(r"```.*?```", "", s, flags=re.S)
    s = re.sub(r"`([^`]*)`", r"\1", s)
    # remove images and links keeping alt/text
    s = re.sub(r"!\[([^\]]*)\]\([^\)]*\)", r"\1", s)
    s = re.sub(r"\[([^\]]*)\]\([^\)]*\)", r"\1", s)
    # remove headings, emphasis, bullets, HTML tags
    s = re.sub(r"(^|\n)#+\s*", r"\1", s)
    s = re.sub(r"[*_~]{1,3}", "", s)
    s = re.sub(r"[-*]\s+", "", s)
    s = re.sub(r"<[^>]+>", "", s)
    # compress whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _short_text(text: str, length: int = 240) -> str:
    txt = _strip_md(text or "")
    if len(txt) <= length:
        return txt
    # cut at last space before limit
    cut = txt[:length].rsplit(" ", 1)[0]
    return cut + "…"


def _fullname_for_person(obj) -> str:
    # Accept either full_name or name+surname fields
    fn = getattr(obj, "full_name", None)
    if fn:
        return fn
    name = (getattr(obj, "name", "") or "").strip()
    surname = (getattr(obj, "surname", "") or "").strip()
    return f"{name} {surname}".strip()


def _speaker_to_dict(s) -> dict:
    return {
        "id": getattr(s, "id", None),
        "fullname": _fullname_for_person(s) or "",
        "position": getattr(s, "position", "") or "",
        "company": getattr(s, "company", "") or "",
        "photo_url": _resolve_media(getattr(s, "photo", None)),
    }


def _moderator_to_dict(m) -> dict:
    return {
        "id": getattr(m, "id", None),
        "fullname": _fullname_for_person(m) or "",
        "position": getattr(m, "position", "") or "",
        "company": getattr(m, "company", "") or "",
        "description_norm": getattr(m, "description", "") or "",
        "photo_url": _resolve_media(getattr(m, "photo", None)),
    }


def _sponsor_to_dict(sp) -> dict:
    return {
        "id": getattr(sp, "id", None),
        "name": getattr(sp, "name", "") or "",
        "logo_url": _resolve_media(getattr(sp, "logo", None)),
        "tier": (getattr(sp, "tier", "") or "").lower(),
    }


def _choose_top_sponsor(sponsors: Iterable) -> Optional[dict]:
    """Pick the first sponsor in the given order; return None if empty."""
    s_list = [_sponsor_to_dict(sp) for sp in sponsors or []]
    return s_list[0] if s_list else None


def episode_to_view(ep: Episode) -> dict:
    """
    Convert Episode SQLAlchemy model instance to a dict suitable for templates:
    - short_desc: short text preview of description_md
    - topic_desc: topic or topic_desc field if present (fallback to empty)
    - top_sponsor: dict or None
    - speakers/moderators: lists of dicts with resolved photo urls
    """
    # base fields (keep start_time/end_time as datetimes)
    base = {
        "id": getattr(ep, "id", None),
        "slug": getattr(ep, "slug", "") or "",
        "title": getattr(ep, "title", "") or "",
        "description_md": getattr(ep, "description_md", "") or "",
        "short_desc": _short_text(getattr(ep, "short_desc", None) or getattr(ep, "description_md", "") or "", 240),
        "topic_desc": getattr(ep, "topic_desc", "") or getattr(ep, "topic", "") or "",
        "start_time": getattr(ep, "start_time", None),
        "end_time": getattr(ep, "end_time", None),
        "location": getattr(ep, "location", "") or "",
        "published": bool(getattr(ep, "published", True)),
        "sort_order": getattr(ep, "sort_order", None),
        "hero_image_url": _resolve_media(getattr(ep, "hero_image_url", None)),
        "day_id": getattr(ep, "day_id", None),
        "site_id": getattr(ep, "site_id", None),
    }

    # speakers / moderators / sponsors (use safe getattr)
    speakers = getattr(ep, "speakers", []) or []
    moderators = getattr(ep, "moderators", []) or []
    sponsors = getattr(ep, "sponsors", []) or []

    base["speakers"] = [_speaker_to_dict(s) for s in speakers]
    base["moderators"] = [_moderator_to_dict(m) for m in moderators]
    base["sponsors"] = [_sponsor_to_dict(s) for s in sponsors]
    base["top_sponsor"] = _choose_top_sponsor(sponsors)

    # convenience: first moderator (so templates that used mod = moderators[0] can still work)
    base["first_moderator"] = base["moderators"][0] if base["moderators"] else None

    return base


def list_days_with_episode_views(
    *,
    site_id: Optional[int] = None,
    only_published: bool = True,
) -> List[dict]:
    """
    Similar to previous list_days_with_episodes but returns episodes already converted
    via episode_to_view.
    """
    from app.services.agenda import list_days, list_episodes_for_day

    out = []
    days = list_days(site_id=site_id, only_published=only_published)
    for d in days:
        eps = list_episodes_for_day(day_id=d["id"], site_id=site_id, only_published=only_published)
        evs = []
        for e in eps:
            if hasattr(e, "__dict__") and (hasattr(e, "speakers") or hasattr(e, "moderators")):
                evs.append(episode_to_view(e))
            else:
                ev = {
                    "id": e.get("id"),
                    "slug": e.get("slug", ""),
                    "title": e.get("title", "") or "",
                    "description_md": e.get("description_md", "") or "",
                    "short_desc": e.get("short_desc") or _short_text(e.get("description_md", "") or "", 240),
                    "topic_desc": e.get("topic_desc") or "",
                    "start_time": e.get("start_time"),
                    "end_time": e.get("end_time"),
                    "location": e.get("location") or "",
                    "published": bool(e.get("published", True)),
                    "sort_order": e.get("sort_order", None),
                    "hero_image_url": _resolve_media(e.get("hero_image_url")),
                    "day_id": e.get("day_id"),
                    "site_id": e.get("site_id"),
                    # map nested lists
                    "speakers": [{
                        "id": s.get("id"),
                        "fullname": s.get("fullname"),
                        "position": s.get("position"),
                        "company": s.get("company"),
                        "photo_url": _resolve_media(s.get("photo_url") or s.get("photo")),
                    } for s in (e.get("speakers") or [])],
                    "moderators": [{
                        "id": m.get("id"),
                        "fullname": m.get("fullname"),
                        "position": m.get("position"),
                        "company": m.get("company"),
                        "description_norm": m.get("description") or m.get("description_norm", ""),
                        "photo_url": _resolve_media(m.get("photo_url") or m.get("photo")),
                    } for m in (e.get("moderators") or [])],
                    "sponsors": [_sponsor_to_dict(s) for s in (e.get("sponsors") or [])],
                }
                ev["top_sponsor"] = _choose_top_sponsor(e.get("sponsors") or [])
                ev["first_moderator"] = ev["moderators"][0] if ev["moderators"] else None
                evs.append(ev)
        out.append({**d, "episodes": evs})
    return out
