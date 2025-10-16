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
from app.models.participant_model import (  # adjust path if different
    Participant, ParticipantRole)


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
    """Render Markdown to HTML5. Falls back to simple paragraphizer on errors."""
    if not md_text:
        return ""
    norm = normalize_markdown(md_text)
    try:
        return _md_lib.markdown(
            norm,
            extensions=["extra", "sane_lists", "toc", "attr_list", "nl2br"],
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
    # Provide a sensible default avatar/logo
    return _resolve_media(logo) if logo else "/static/img/default_participant.png"


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
    return f"<p>{first}</p>"


# -----------------------------
# Public API
# -----------------------------
def list_participants(
        *,
        limit: int = 24,
        latest_first: bool = True,
        site_id: Optional[int] = None,
        role: Optional[str] = None,  # "expo" | "forum" | "both"
        q: Optional[str] = None,  # simple name search
) -> list[dict]:
    """
    List participants for list/grid pages.
    """
    with _db_session() as db:
        stmt = select(Participant)

        if site_id:
            stmt = stmt.where(Participant.site_id == site_id)

        if role:
            role_val = role.lower().strip()
            if role_val == "expo":
                stmt = stmt.where(Participant.role.in_(("expo", "both")))
            elif role_val == "forum":
                stmt = stmt.where(Participant.role.in_(("forum", "both")))
            elif role_val == "both":
                stmt = stmt.where(Participant.role == "both")
            else:
                # ignore unknown role
                pass

        if q:
            # lightweight ILIKE search on name
            from sqlalchemy import or_
            stmt = stmt.where(or_(Participant.name.ilike(f"%{q}%")))

        order = desc(Participant.created_at) if latest_first else asc(Participant.created_at)
        rows = db.execute(stmt.order_by(order).limit(limit)).scalars().all()

        out: list[dict] = []
        for r in rows:
            # images relationship uses selectin; available as list of ParticipantImage
            gallery = getattr(r, "images", None)
            images = _resolve_image_list(gallery)
            out.append({
                "id": r.id,
                "name": r.name,
                "role": getattr(r.role, "value", r.role) if r.role else None,
                "bio": r.bio,
                "logo_url": _resolve_logo_url(getattr(r, "logo", None)),
                "images": images[:3],
            })
        return out


def get_participant(
    *,
    participant_id: int,
    site_id: Optional[int] = None,
) -> Optional[dict]:
    """
    Detail payload for a single participant.
    """
    with _db_session() as db:
        stmt = select(Participant).where(Participant.id == participant_id)
        if site_id:
            stmt = stmt.where(Participant.site_id == site_id)

        r = db.execute(stmt).scalars().first()
        if not r:
            return None

        bio = getattr(r, "bio", None) or ""
        intro_html = _first_paragraph_html(bio)
        body_html = md_to_html(bio)

        gallery = getattr(r, "images", None)
        all_images = _resolve_image_list(gallery)
        images_hero = all_images[:3]
        images_rest = all_images[3:]

        return {
            "id": r.id,
            "name": r.name,
            "role": getattr(r.role, "value", r.role) if r.role else None,
            "bio": bio,
            "intro_html": intro_html,
            "body_html": body_html,
            "logo_url": _resolve_logo_url(getattr(r, "logo", None)),
            "images_hero": images_hero,
            "images_rest": images_rest,
            "created_at": r.created_at,
            "updated_at": r.updated_at,
        }
