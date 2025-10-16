# app/services/sponsors.py
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

# ---- NEW: presentation helpers ------------------------------------------------

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
    # top tiers don’t need a color class, but keep keys for completeness
    "premier": "",
    "general": "",
    "diamond": "",
    "platinum": "",
}


def tier_label(tier: str) -> str:
    return _TIER_LABELS.get(tier, f"{tier.capitalize()} Sponsor")


def tier_css_class(tier: str) -> str:
    return _TIER_CLASSES.get(tier, "")


# -----------------------------------------------------------------------------


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
    # If already absolute (http/https), keep it
    if u.lower().startswith(("http://", "https://")):
        return u
    # If it looks like a scheme-less domain, prefix https
    # Avoid double slashes if someone typed "/google.com"
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
        # helpful presentation fields (safe to ignore in old templates)
        "tier_label": tier_label(tier_val),
        "tier_class": tier_css_class(tier_val),
    }


def get_top_sponsors(
    *,
    lang: str = "en",
    site_id: Optional[int] = None,
    per_tier_limit: Optional[int] = None,
) -> dict[TopTier, list[dict]]:
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
            stmt = stmt.order_by(asc(Sponsor.id))
            if per_tier_limit and per_tier_limit > 0:
                stmt = stmt.limit(per_tier_limit)
            try:
                rows = db.execute(stmt).scalars().all()
            except DataError:
                rows = []
            out[t] = [_project(sp) for sp in rows] if rows else []
    return out


def get_top_sponsors_flat(
    *,
    lang: str = "en",
    site_id: Optional[int] = None,
    max_items: int = 5,
) -> dict:
    # (kept for backward compatibility with your current template)
    order: list[TopTier] = ["premier", "general", "diamond", "platinum"]
    grouped = get_top_sponsors(lang=lang, site_id=site_id)
    flat: list[dict] = []
    for t in order:
        for sp in grouped.get(t, []):
            flat.append(sp)
            if len(flat) >= max_items:
                return {"items": flat[:max_items], "count": min(len(flat), max_items)}
    return {"items": flat[:max_items], "count": len(flat[:max_items])}


# ---- NEW: HTML-logic extracted into service ----------------------------------


def build_top_sponsors_view(
        *,
        lang: str = "en",
        site_id: Optional[int] = None,
        max_items: int = 5,  # mirrors MAX in _sponsors_top.html
) -> dict:
    """
    Decides whether to show grid or marquee for top sponsors and returns only the required data.
    """
    flat = get_top_sponsors_flat(lang=lang, site_id=site_id, max_items=max_items)
    items = flat.get("items", [])
    count = len(items)

    layout: Literal["empty", "grid", "marquee"]
    if count == 0:
        layout = "empty"
    elif count < max_items:
        layout = "grid"
    else:
        layout = "marquee"

    # view model used directly by the template
    return {
        "layout": layout,
        "items": items,  # already trimmed/ordered
        "count": count,
        "max": max_items,
        # classes used across cards
        "card_base_class": "bg-white rounded-2xl shadow p-4 flex flex-col items-center justify-between h-[276px]",
        "card_interactive_suffix": " border border-transparent transition-all duration-300 group-hover:shadow-lg group-hover:border-[var(--c-primary)]",
        "link_interactive_class": "group block focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--c-primary)] rounded-2xl",
        "placeholder_src": "/static/img/img_placeholder.png",
        "img_w": 202,
        "img_h": 202,
    }


def list_all_sponsors_by_tier(
    *,
    tier: ListTier,
    lang: str = "en",
    site_id: Optional[int] = None,
) -> dict:
    """
    Backward compatible: still returns {"items": [...], "tier": tier}
    PLUS presentation keys so the template doesn’t have to slice or decide layout.
    """
    try:
        enum_val = SponsorTier(tier)
    except ValueError:
        return {
            "items": [],
            "tier": tier,
            "count": 0,
            "tier_label": tier_label(tier),
            "tier_class": tier_css_class(tier),
            "layout": "empty",
            "rows": [],
            "marquee_rows": [],
        }

    with _db_session() as db:
        stmt = select(Sponsor).where(Sponsor.tier == enum_val)
        if site_id is not None:
            stmt = stmt.where(Sponsor.site_id == site_id)
        stmt = stmt.order_by(asc(Sponsor.id))
        try:
            items = db.execute(stmt).scalars().all()
        except DataError:
            items = []

    projected = [_project(sp) for sp in items]
    count = len(projected)

    # decide layout for carousel
    # - 0: empty
    # - 1..10: two static rows (5 + 5)
    # - >10: two marquee rows, split odd/even indices
    if count == 0:
        layout = "empty"
        rows: list[list[dict]] = []
        marquee_rows: list[list[dict]] = []
    elif count <= 10:
        layout = "rows"
        rows = [projected[:5], projected[5:10]]
        marquee_rows = []
    else:
        layout = "marquee"
        marquee_rows = [projected[0::2], projected[1::2]]
        rows = []

    return {
        "items": projected,  # kept for compatibility
        "tier": tier,
        "count": count,
        "tier_label": tier_label(tier),
        "tier_class": tier_css_class(tier),
        "layout": layout,
        "rows": rows,
        "marquee_rows": marquee_rows,
        # shared presentation defaults for cards in this block
        "card_base_class": "bg-white rounded-2xl shadow p-4 w-[190px] h-[225px] flex flex-col items-center justify-start",
        "card_interactive_suffix": " border border-transparent transition-all duration-300 group-hover:shadow-lg group-hover:border-[var(--c-primary)]",
        "link_interactive_class": "group block focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--c-primary)] rounded-2xl",
        "placeholder_src": "/static/img/img_placeholder.png",
        "img_w": 150,
        "img_h": 150,
    }
