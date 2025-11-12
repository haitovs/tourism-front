# app/services/sponsors.py
from __future__ import annotations

import asyncio
from contextlib import contextmanager
from functools import partial
from typing import Generator, Literal, Optional
from urllib.parse import urljoin

from sqlalchemy import asc, select
from sqlalchemy.exc import DataError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.settings import settings
from app.models.sponsor_model import Sponsor, SponsorTier
from app.utils.timed_cache import TimedCache

TopTier = Literal["premier", "general", "diamond", "platinum"]
ListTier = Literal["gold", "silver", "bronze"]

_TIER_LABELS: dict[str, str] = {
    "gold": "Gold Sponsor",
    "silver": "Silver Sponsor",
    "bronze": "Bronze Sponsor",
    "premier": "Premier Sponsor",
    "general": "General Sponsor",
    "diamond": "Diamond Sponsor",
    "platinum": "Platinum Sponsor",
}

_TIER_CLASSES: dict[str, str] = {
    # used by _sponsors_carousel.html
    "gold": "tier-gold",
    "silver": "tier-silver",
    "bronze": "tier-bronze",
    "premier": "",
    "general": "",
    "diamond": "",
    "platinum": "",
}

_PROJECTED_CACHE = TimedCache(ttl_seconds=60.0)


def tier_label(tier: str) -> str:
    return _TIER_LABELS.get(tier, f"{tier.capitalize()} Sponsor")


def tier_css_class(tier: str) -> str:
    return _TIER_CLASSES.get(tier, "")


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


def _normalize_website(url: str | None) -> str:
    if not url:
        return ""
    u = url.strip()
    if u.lower().startswith(("http://", "https://")):
        return u
    u = u.lstrip("/")
    return f"https://{u}"


def _resolve_logo_url(logo: str | None) -> str:
    if not logo:
        return ""
    low = logo.lower()
    if low.startswith("http://") or low.startswith("https://"):
        return logo
    base = settings.MEDIA_BASE_URL.rstrip("/") + "/"
    if logo.startswith("/"):
        return urljoin(base, logo.lstrip("/"))
    pref = settings.MEDIA_PREFIX.strip("/")
    path = f"{pref}/{logo.lstrip('/')}"
    return urljoin(base, path)


def _project(sp: Sponsor) -> dict:
    if not sp:
        return {}
    tier_val = sp.tier.value if isinstance(sp.tier, SponsorTier) else str(sp.tier)
    return {
        "id": sp.id,
        "name": sp.name,
        "website": _normalize_website(sp.website),
        "logo_url": _resolve_logo_url(sp.logo),
        "tier": tier_val,
        "tier_label": tier_label(tier_val),
        "tier_class": tier_css_class(tier_val),
    }


async def _run_in_thread(fn, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(fn, *args, **kwargs))


def _load_projected_sync(site_id: Optional[int]) -> list[dict]:
    with _db_session() as db:
        stmt = select(Sponsor)
        if site_id is not None:
            stmt = stmt.where(Sponsor.site_id == site_id)
        stmt = stmt.order_by(asc(Sponsor.id))
        try:
            rows = db.execute(stmt).scalars().all()
        except DataError:
            rows = []
    return [_project(sp) for sp in rows]


async def _load_projected_sponsors(site_id: Optional[int]) -> list[dict]:
    cache_key = f"projected:{site_id or 'all'}"
    cached = _PROJECTED_CACHE.get(cache_key)
    if cached is not None:
        return cached
    rows = await _run_in_thread(_load_projected_sync, site_id)
    _PROJECTED_CACHE.set(cache_key, rows)
    return rows


async def get_top_sponsors(
    *,
    lang: str = "en",
    site_id: Optional[int] = None,
    per_tier_limit: Optional[int] = None,
) -> dict[TopTier, list[dict]]:
    tiers: list[TopTier] = ["premier", "general", "diamond", "platinum"]
    out: dict[TopTier, list[dict]] = {t: [] for t in tiers}
    rows = await _load_projected_sponsors(site_id)

    per_limit = max(1, per_tier_limit) if per_tier_limit else None
    for t in tiers:
        tier_items = [sp for sp in rows if sp.get("tier") == t]
        if per_limit:
            tier_items = tier_items[:per_limit]
        out[t] = tier_items
    return out


async def get_top_sponsors_flat(
    *,
    lang: str = "en",
    site_id: Optional[int] = None,
    max_items: int = 5,
) -> dict:
    order: list[TopTier] = ["premier", "general", "diamond", "platinum"]
    grouped = await get_top_sponsors(lang=lang, site_id=site_id)
    flat: list[dict] = []
    for t in order:
        for sp in grouped.get(t, []):
            flat.append(sp)
            if len(flat) >= max_items:
                return {"items": flat[:max_items], "count": min(len(flat), max_items)}
    return {"items": flat[:max_items], "count": len(flat[:max_items])}


async def build_top_sponsors_view(
    *,
    lang: str = "en",
    site_id: Optional[int] = None,
    max_items: int = 5,
) -> dict:
    """
    Decides whether to show grid or marquee for top sponsors and returns only the required data.
    """
    flat = await get_top_sponsors_flat(lang=lang, site_id=site_id, max_items=max_items)
    items = flat.get("items", [])
    count = len(items)

    layout: Literal["empty", "grid", "marquee"]
    if count == 0:
        layout = "empty"
    elif count < max_items:
        layout = "grid"
    else:
        layout = "marquee"

    return {
        "layout": layout,
        "items": items,
        "count": count,
        "max": max_items,
        "card_base_class": "bg-white rounded-2xl shadow p-4 flex flex-col items-center justify-between h-[276px]",
        "card_interactive_suffix": " border border-transparent transition-all duration-300 group-hover:shadow-lg group-hover:border-[var(--c-primary)]",
        "link_interactive_class": "group block focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--c-primary)] rounded-2xl",
        "placeholder_src": "/static/img/img_placeholder.png",
        "img_w": 202,
        "img_h": 202,
    }


async def list_all_sponsors_by_tier(
    *,
    tier: ListTier,
    lang: str = "en",
    site_id: Optional[int] = None,
) -> dict:
    rows = await _load_projected_sponsors(site_id)
    projected = [sp for sp in rows if sp.get("tier") == tier]
    count = len(projected)

    if count == 0:
        layout = "empty"
        rows_layout: list[list[dict]] = []
        marquee_rows: list[list[dict]] = []
    elif count <= 10:
        layout = "rows"
        rows_layout = [projected[:5], projected[5:10]]
        marquee_rows = []
    else:
        layout = "marquee"
        marquee_rows = [projected[0::2], projected[1::2]]
        rows_layout = []

    return {
        "items": projected,
        "tier": tier,
        "count": count,
        "tier_label": tier_label(tier),
        "tier_class": tier_css_class(tier),
        "layout": layout,
        "rows": rows_layout,
        "marquee_rows": marquee_rows,
        "card_base_class": "bg-white rounded-2xl shadow p-4 h-[225px] flex flex-col items-center justify-start",
        "card_interactive_suffix": " border border-transparent transition-all duration-300 group-hover:shadow-lg group-hover:border-[var(--c-primary)]",
        "link_interactive_class": "group block focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--c-primary)] rounded-2xl",
        "placeholder_src": "/static/img/img_placeholder.png",
        "img_w": 150,
        "img_h": 150,
    }


async def get_homepage_bundle(
    *,
    lang: str = "en",
    site_id: Optional[int] = None,
    max_top_items: int = 5,
) -> dict:
    sponsors_top = await get_top_sponsors(lang=lang, site_id=site_id)
    sponsors_top_flat = await get_top_sponsors_flat(lang=lang, site_id=site_id, max_items=max_top_items)
    sponsors_top_view = await build_top_sponsors_view(lang=lang, site_id=site_id, max_items=max_top_items)
    gold = await list_all_sponsors_by_tier(tier="gold", lang=lang, site_id=site_id)
    silver = await list_all_sponsors_by_tier(tier="silver", lang=lang, site_id=site_id)
    bronze = await list_all_sponsors_by_tier(tier="bronze", lang=lang, site_id=site_id)
    return {
        "sponsors_top": sponsors_top,
        "sponsors_top_flat": sponsors_top_flat,
        "sponsors_top_view": sponsors_top_view,
        "gold": gold,
        "silver": silver,
        "bronze": bronze,
    }
