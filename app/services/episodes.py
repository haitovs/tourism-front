from __future__ import annotations

import re
from datetime import datetime as _dt
from typing import Any, Dict, List, Optional, Tuple

from fastapi import Request

from app.core.http import abs_media, api_get
from app.core.settings import settings
from app.models.episode_model import Episode
from app.services.agenda import list_days, list_episodes_for_day

# ---------------- utils ----------------


def _to_dt(val):
    if isinstance(val, _dt):
        return val
    if isinstance(val, str):
        s = val.strip().replace("Z", "+00:00")
        if " " in s and "T" not in s:
            s = s.replace(" ", "T")
        try:
            return _dt.fromisoformat(s)
        except Exception:
            return None
    return None


def _resolve_media(path: Optional[str]) -> str:
    return abs_media(path)


def _strip_md(text: str) -> str:
    if not text:
        return ""
    s = text
    s = re.sub(r"```.*?```", "", s, flags=re.S)
    s = re.sub(r"`([^`]*)`", r"\1", s)
    s = re.sub(r"!\[([^\]]*)\]\([^\)]*\)", r"\1", s)
    s = re.sub(r"\[([^\]]*)\]\([^\)]*\)", r"\1", s)
    s = re.sub(r"(^|\n)#+\s*", r"\1", s)
    s = re.sub(r"[*_~]{1,3}", "", s)
    s = re.sub(r"[-*]\s+", "", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _short_text(text: str, length: int = 240) -> str:
    t = _strip_md(text or "")
    if len(t) <= length:
        return t
    cut = t[:length].rsplit(" ", 1)[0]
    return cut + "…"


def _as_int(val) -> Optional[int]:
    if isinstance(val, int):
        return val
    if isinstance(val, str) and val.strip().isdigit():
        return int(val.strip())
    return None


def _norm(s: Optional[str]) -> str:
    return (s or "").strip().lower()


def _first_nonempty_str(*values: Any) -> str:
    for val in values:
        if isinstance(val, str):
            txt = val.strip()
            if txt:
                return txt
    return ""


def _lang_candidates(*hints: Any) -> List[str]:
    langs: List[str] = []
    for hint in hints:
        if not isinstance(hint, str):
            continue
        base = hint.strip()
        if not base:
            continue
        base = base.split("-", 1)[0].lower()
        if base and base not in langs:
            langs.append(base)
    default_lang = (settings.DEFAULT_LANG or "").split("-", 1)[0].lower()
    if default_lang and default_lang not in langs:
        langs.append(default_lang)
    if "en" not in langs:
        langs.append("en")
    return langs


def _extract_localized_text(value: Any, languages: List[str]) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in languages:
            if key in value:
                candidate = _extract_localized_text(value[key], languages)
                if candidate:
                    return candidate
        for key in ("value", "text", "content", "description", "body", "message"):
            if key in value:
                candidate = _extract_localized_text(value[key], languages)
                if candidate:
                    return candidate
        for sub_val in value.values():
            candidate = _extract_localized_text(sub_val, languages)
            if candidate:
                return candidate
        return ""
    if isinstance(value, (list, tuple, set)):
        for item in value:
            candidate = _extract_localized_text(item, languages)
            if candidate:
                return candidate
    return ""


def _coalesce_description_fields(data: Dict[str, Any]) -> Tuple[str, str]:
    lang_hint = data.get("lang") or data.get("language") or data.get("locale") or data.get("preferred_language")
    languages = _lang_candidates(lang_hint)

    plain = _first_nonempty_str(
        data.get("description"),
        data.get("bio"),
        data.get("description_plain"),
        data.get("bio_plain"),
    )
    if not plain:
        plain = _extract_localized_text(
            data.get("description_i18n")
            or data.get("description_translations")
            or data.get("description_localized")
            or data.get("bio_i18n")
            or data.get("description_localizations")
            or data.get("descriptionLocales"),
            languages,
        )

    html = _first_nonempty_str(
        data.get("description_html"),
        data.get("bio_html"),
        data.get("description_richtext"),
        data.get("bio_richtext"),
    )
    if not html:
        html = _extract_localized_text(
            data.get("description_html_i18n")
            or data.get("bio_html_i18n")
            or data.get("description_html_translations"),
            languages,
        )

    if not html:
        html = plain

    return plain.strip(), html.strip()


def _fullname_for_person(obj) -> str:
    fn = getattr(obj, "full_name", None) or getattr(obj, "fullname", None)
    if fn:
        return fn
    name = (getattr(obj, "name", "") or "").strip()
    surname = (getattr(obj, "surname", "") or "").strip()
    return f"{name} {surname}".strip()


def _flatten_person_like(x: dict) -> dict:
    if not isinstance(x, dict):
        return {}
    inner = x.get("person") or x.get("speaker") or x.get("moderator") or {}
    merged = {**x, **inner} if isinstance(inner, dict) else x
    fullname = merged.get("fullname") or f"{(merged.get('name') or '').strip()} {(merged.get('surname') or '').strip()}".strip()
    photo_url = _resolve_media(merged.get("photo_url") or merged.get("photo"))
    desc_plain, desc_html = _coalesce_description_fields(merged)
    desc_norm = _strip_md(desc_plain or desc_html)
    return {
        "id": _as_int(merged.get("id")),
        "fullname": fullname or "",
        "position": merged.get("position") or "",
        "company": merged.get("company") or "",
        "description": desc_plain,
        "description_html": desc_html,
        "description_norm": desc_norm,
        "photo_url": photo_url,
    }


def _flatten_sponsor_like(x: dict) -> dict:
    if not isinstance(x, dict):
        return {}
    inner = x.get("sponsor") or x.get("partner") or {}
    merged = {**x, **inner} if isinstance(inner, dict) else x
    return {
        "id": _as_int(merged.get("id")),
        "name": merged.get("name") or "",
        "logo_url": _resolve_media(merged.get("logo_url") or merged.get("logo")),
        "tier": (merged.get("tier") or "").lower(),
        "url": merged.get("url") or merged.get("website") or merged.get("link"),
    }


def _sponsor_from_episode(e: Dict[str, Any]) -> Optional[dict]:
    sp = e.get("top_sponsor") or e.get("sponsor")
    return _flatten_sponsor_like(sp) if isinstance(sp, dict) else None


async def _safe_get(req: Request, path: str):
    try:
        return await api_get(req, path)
    except Exception:
        return None


# ---------------- ORM mapper (kept for safety) ----------------


def episode_to_view(ep: Episode) -> dict:
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
    speakers = getattr(ep, "speakers", []) or []
    moderators = getattr(ep, "moderators", []) or []
    sponsors = getattr(ep, "sponsors", []) or []

    base["speakers"] = [_flatten_person_like(s.__dict__ if hasattr(s, "__dict__") else s) for s in speakers]
    base["moderators"] = [_flatten_person_like(m.__dict__ if hasattr(m, "__dict__") else m) for m in moderators]
    base["sponsors"] = [_flatten_sponsor_like(s.__dict__ if hasattr(s, "__dict__") else s) for s in sponsors]
    base["top_sponsor"] = base["sponsors"][0] if base["sponsors"] else None
    base["first_moderator"] = base["moderators"][0] if base["moderators"] else None
    return base


# ---------------- matching helpers ----------------


def _episode_indices(eps: List[dict]) -> Tuple[Dict[int, dict], Dict[str, dict], Dict[str, dict]]:
    by_id: Dict[int, dict] = {}
    by_slug: Dict[str, dict] = {}
    by_title: Dict[str, dict] = {}
    for ev in eps:
        eid = _as_int(ev.get("id"))
        if eid is not None:
            by_id[eid] = ev
        slug = _norm(ev.get("slug"))
        if slug:
            by_slug[slug] = ev
        title = _norm(ev.get("title"))
        if title:
            by_title[title] = ev
    return by_id, by_slug, by_title


def _extract_episode_keys_from_value(value) -> Tuple[List[int], List[str], List[str]]:
    ids: List[int] = []
    slugs: List[str] = []
    titles: List[str] = []

    def acc(v):
        if v is None:
            return
        if isinstance(v, (int, str)):
            iv = _as_int(v)
            if iv is not None:
                ids.append(iv)
        elif isinstance(v, dict):
            iv = _as_int(v.get("id") or v.get("episode_id") or v.get("session_id"))
            if iv is not None:
                ids.append(iv)
            s = _norm(v.get("slug") or v.get("episode_slug") or v.get("session_slug"))
            t = _norm(v.get("title") or v.get("episode_title") or v.get("session_title"))
            if s:
                slugs.append(s)
            if t:
                titles.append(t)
        elif isinstance(v, list):
            for it in v:
                acc(it)

    acc(value)

    def dedupe(seq):
        seen, out = set(), []
        for x in seq:
            if x not in seen:
                out.append(x)
                seen.add(x)
        return out

    return dedupe(ids), dedupe(slugs), dedupe(titles)


def _attach_people_from_rows(rows: List[dict], evs: List[dict], role: str):
    by_id, by_slug, by_title = _episode_indices(evs)
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        person = _flatten_person_like(row)
        if not (person.get("fullname") or person.get("id")):
            continue

        # Speakers service uses "sessions"; accept many fallbacks
        session_val = (row.get("sessions") or row.get("episodes") or row.get("episode_ids") or row.get("session_ids") or row.get("session") or row.get("episode"))
        ids, slugs, titles = _extract_episode_keys_from_value(session_val)

        matched: List[dict] = []
        for eid in ids:
            ev = by_id.get(eid)
            if ev:
                matched.append(ev)
        if not matched:
            for s in slugs:
                ev = by_slug.get(s)
                if ev:
                    matched.append(ev)
        if not matched:
            for t in titles:
                ev = by_title.get(t)
                if ev:
                    matched.append(ev)

        if not matched:
            continue

        for ev in matched:
            bucket = ev["speakers"] if role == "speaker" else ev["moderators"]
            if not any((p.get("id") and p.get("id") == person.get("id")) or (p.get("fullname") == person.get("fullname")) for p in bucket):
                bucket.append(person)
            if role == "moderator" and not ev.get("first_moderator"):
                ev["first_moderator"] = person


# ---------------- main list ----------------


async def list_days_with_episode_views(
    req: Request,
    *,
    site_id: Optional[int] = None,
    only_published: bool = True,
) -> List[dict]:
    import asyncio
    import logging
    log = logging.getLogger("services.agenda.compose")

    # Fetch days + people lists concurrently
    days_task = asyncio.create_task(list_days(req, site_id=site_id, only_published=only_published))
    speakers_task = asyncio.create_task(_safe_get(req, "/speakers/"))
    moderators_task = asyncio.create_task(_safe_get(req, "/moderators/"))

    days, speakers_rows, moderators_rows = await asyncio.gather(days_task, speakers_task, moderators_task)
    speakers_rows = speakers_rows if isinstance(speakers_rows, list) else []
    moderators_rows = moderators_rows if isinstance(moderators_rows, list) else []

    out: List[dict] = []
    if not days:
        return out

    # Fetch all episodes for all days concurrently
    ep_tasks = [asyncio.create_task(list_episodes_for_day(req, day_id=d["id"], site_id=site_id, only_published=only_published)) for d in days if d and d.get("id") is not None]
    ep_results = await asyncio.gather(*ep_tasks, return_exceptions=True)

    # Map day -> episodes safely
    day_to_eps: List[List[dict]] = []
    i = 0
    for d in days:
        if d and d.get("id") is not None:
            res = ep_results[i]
            i += 1
            if isinstance(res, Exception):
                log.warning("episodes for day %s failed: %r", d.get("id"), res)
                day_to_eps.append([])
            else:
                day_to_eps.append(res or [])
        else:
            day_to_eps.append([])

    # Build views and attach speakers/moderators
    for d, raw_eps in zip(days, day_to_eps):
        evs: List[dict] = []
        for e in raw_eps or []:
            ev = {
                "id": _as_int(e.get("id")),
                "slug": e.get("slug", "") or "",
                "title": e.get("title", "") or "",
                "description_md": e.get("description_md", "") or "",
                "short_desc": _short_text(e.get("short_desc") or e.get("description_md") or "", 240),
                "topic_desc": e.get("topic_desc") or e.get("topic", "") or "",
                "start_time": _to_dt(e.get("start_time")),
                "end_time": _to_dt(e.get("end_time")),
                "location": e.get("location") or "",
                "published": bool(e.get("published", True)),
                "sort_order": e.get("sort_order", None),
                "hero_image_url": _resolve_media(e.get("hero_image_url")),
                "day_id": e.get("day_id"),
                "site_id": e.get("site_id"),
                "speakers": [_flatten_person_like(s) for s in (e.get("speakers") or []) if isinstance(s, dict)],
                "moderators": [_flatten_person_like(m) for m in (e.get("moderators") or []) if isinstance(m, dict)],
                "sponsors": [_flatten_sponsor_like(sp) for sp in (e.get("sponsors") or []) if isinstance(sp, dict)],
            }

            if not ev["moderators"]:
                fm = e.get("first_moderator")
                ev["first_moderator"] = _flatten_person_like(fm) if isinstance(fm, dict) else None
                if ev["first_moderator"]:
                    ev["moderators"] = [ev["first_moderator"]]
            else:
                ev["first_moderator"] = ev["moderators"][0]

            ev["top_sponsor"] = ev["sponsors"][0] if ev["sponsors"] else _sponsor_from_episode(e)
            evs.append(ev)

        _attach_people_from_rows(speakers_rows, evs, role="speaker")
        _attach_people_from_rows(moderators_rows, evs, role="moderator")

        out.append({**d, "episodes": evs})

    return out
