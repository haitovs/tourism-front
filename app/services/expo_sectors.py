from __future__ import annotations

import re
from collections.abc import Iterable
from contextlib import contextmanager
from typing import Generator, Optional
from urllib.parse import urljoin

import markdown as _md_lib
from sqlalchemy import asc, desc, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.settings import settings
from app.models.expo_sector_model import ExpoSector


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


_bullet_like = re.compile(r"(\S)\s-\s+")


def normalize_markdown(md_text: str) -> str:
    """Make common inline patterns parseable as Markdown lists/headings."""
    if not md_text:
        return ""
    txt = md_text.replace("\r\n", "\n").replace("\r", "\n")
    txt = re.sub(r"([^\n])(\n?)(\s*#{1,6}\s+)", r"\1\n\n\3", txt)
    txt = re.sub(r":\s+-\s+", ":\n- ", txt)
    txt = _bullet_like.sub(r"\1\n- ", txt)
    txt = re.sub(r"([^\n])\n(-\s+)", r"\1\n\n\2", txt)

    return txt


def md_to_html(md_text: str) -> str:
    """Render Markdown to HTML5. Falls back to a simple paragraphizer on errors."""
    if not md_text:
        return ""
    norm = normalize_markdown(md_text)
    try:
        return _md_lib.markdown(
            norm,
            extensions=[
                "extra",
                "sane_lists",
                "toc",
                "attr_list",
                "nl2br",
            ],
            output_format="html5",
        )
    except Exception:
        blocks = [b.strip() for b in norm.strip().split("\n\n") if b.strip()]
        html_blocks = ["<p>{}</p>".format(b.replace("\n", "<br>")) for b in blocks]
        return "".join(html_blocks)


def _resolve_media(url: str | None) -> str:
    if not url:
        return ""
    low = url.lower()
    if low.startswith("http://") or low.startswith("https://"):
        return url
    base = settings.MEDIA_BASE_URL.rstrip("/") + "/"
    return urljoin(base, url.lstrip("/"))


def _resolve_logo_url(logo: str | None) -> str:
    return _resolve_media(logo) if logo else "/static/img/default_sector.png"


def _extract_media_url(obj) -> str:
    """Accepts a string, ORM object, or dict and returns a resolved media URL."""
    if obj is None:
        return ""
    if isinstance(obj, str):
        return _resolve_media(obj)

    for attr in ("url", "image", "file", "path", "src"):
        if hasattr(obj, attr):
            val = getattr(obj, attr)
            if isinstance(val, str) and val:
                return _resolve_media(val)

    if isinstance(obj, dict):
        for key in ("url", "image", "file", "path", "src"):
            val = obj.get(key)
            if isinstance(val, str) and val:
                return _resolve_media(val)

    return ""


def _resolve_image_list(items) -> list[str]:
    """Coerce various ‘images’ shapes to a list of URLs."""
    if not items:
        return []
    if isinstance(items, str):
        items = [items]
    if not isinstance(items, Iterable) or isinstance(items, (bytes, bytearray)):
        return []
    return [u for u in (_extract_media_url(x) for x in items) if u]


def _first_paragraph_html(text: Optional[str]) -> str:
    """Turn the first paragraph of a plain-text field into a <p>…</p> block."""
    if not text:
        return ""
    parts = [p.strip() for p in text.strip().split("\n\n") if p.strip()]
    if not parts:
        return ""
    first = parts[0].replace("\n", "<br>")
    return "<p>{}</p>".format(first)


def list_home_sectors(
    limit: int = 3,
    latest_first: bool = True,
    site_id: Optional[int] = None,
) -> list[dict]:
    with _db_session() as db:
        stmt = select(ExpoSector)
        if site_id:
            stmt = stmt.where(ExpoSector.site_id == site_id)
        order = desc(ExpoSector.created_at) if latest_first else asc(ExpoSector.created_at)
        rows = db.execute(stmt.order_by(order).limit(limit)).scalars().all()

        return [{
            "id": r.id,
            "header": r.header,
            "description": r.description,
            "logo_url": _resolve_logo_url(getattr(r, "logo", None)),
        } for r in rows]


def get_sector(sector_id: int, site_id: Optional[int] = None) -> Optional[dict]:
    with _db_session() as db:
        stmt = select(ExpoSector).where(ExpoSector.id == sector_id)
        if site_id:
            stmt = stmt.where(ExpoSector.site_id == site_id)
        r = db.execute(stmt).scalars().first()
        if not r:
            return None

        header = getattr(r, "header", None)
        subtitle = getattr(r, "subtitle", None)
        description = getattr(r, "description", None)
        extended_md = getattr(r, "extended_description", None)

        hero = getattr(r, "hero", None) or getattr(r, "cover", None)
        tagline = getattr(r, "tagline", None)

        intro_html = _first_paragraph_html(description)
        body_html = md_to_html(extended_md or "")

        gallery = getattr(r, "gallery", None) or getattr(r, "images", None) or getattr(r, "photos", None)
        all_images = _resolve_image_list(gallery)
        images_hero = all_images[:3]
        images_rest = all_images[3:]

        points_left = getattr(r, "points_left", None)
        points_right = getattr(r, "points_right", None)

        return {
            "id": r.id,
            "header": header,
            "subtitle": subtitle,
            "description": description,
            "logo_url": _resolve_logo_url(getattr(r, "logo", None)),
            "hero_url": _resolve_media(hero) if hero else None,
            "tagline": tagline,
            "intro_html": intro_html,
            "body_html": body_html,
            "images_hero": images_hero,
            "images_rest": images_rest,
            "points_left": points_left if isinstance(points_left, list) else None,
            "points_right": points_right if isinstance(points_right, list) else None,
        }
