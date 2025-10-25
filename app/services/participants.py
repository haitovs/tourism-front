# app/services/participants.py
from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any, Optional

import markdown as _md_lib
from fastapi import Request

from app.core.http import _abs_media, api_get
from app.core.settings import settings

_bullet_like = re.compile(r"(\S)\s-\s+")


def normalize_markdown(md_text: str) -> str:
    if not md_text:
        return ""
    txt = md_text.replace("\r\n", "\n").replace("\r", "\n")
    txt = re.sub(r"([^\n])(\n?)(\s*#{1,6}\s+)", r"\1\n\n\3", txt)
    txt = re.sub(r":\s+-\s+", ":\n- ", txt)
    txt = _bullet_like.sub(r"\1\n- ", txt)
    txt = re.sub(r"([^\n])\n(-\s+)", r"\1\n\n\2", txt)
    return txt


def md_to_html(md_text: str) -> str:
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


def _resolve_media(path: str | None) -> str:
    return _abs_media(path)


def _resolve_logo_url(logo: str | None) -> str:
    return _abs_media(logo) if logo else "/static/img/default_participant.png"


def _extract_media_url(obj) -> str:
    if obj is None:
        return ""
    if isinstance(obj, str):
        return _abs_media(obj)
    if isinstance(obj, dict):
        for key in ("url", "image", "file", "path", "src"):
            val = obj.get(key)
            if isinstance(val, str) and val:
                return _abs_media(val)
    return ""


def _resolve_image_list(items) -> list[str]:
    if not items:
        return []
    if isinstance(items, str):
        items = [items]
    if not isinstance(items, Iterable) or isinstance(items, (bytes, bytearray)):
        return []
    return [u for u in (_extract_media_url(x) for x in items) if u]


def _first_paragraph_html(text: Optional[str]) -> str:
    if not text:
        return ""
    parts = [p.strip() for p in text.strip().split("\n\n") if p.strip()]
    if not parts:
        return ""
    first = parts[0].replace("\n", "<br>")
    return f"<p>{first}</p>"


def _unwrap_collection(payload: Any) -> list[dict]:
    """
    Accepts either:
      - a list of dicts
      - or a dict containing items/results/data/etc.
    """
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("items", "results", "data", "participants"):
            val = payload.get(key)
            if isinstance(val, list):
                return val
    return []


def _unwrap_object(payload: Any) -> dict | None:
    """
    Accepts either:
      - a dict (the object itself)
      - a dict like {"data": {...}} or {"item": {...}}
    """
    if payload is None:
        return None
    if isinstance(payload, dict):
        for key in ("data", "item", "participant"):
            v = payload.get(key)
            if isinstance(v, dict):
                return v
        return payload
    return None


# ---------------- LIST PAGE ---------------- #
async def list_participants(
    req: Request,
    *,
    limit: int = 24,
    offset: int = 0,
    latest_first: bool = True,
    role: Optional[str] = None,
    q: Optional[str] = None,
) -> list[dict]:
    rows_raw = await api_get(req, "/participants/") or []
    rows = _unwrap_collection(rows_raw)

    role_norm = (role or "").strip().lower()
    if role_norm in {"expo", "forum", "both"}:

        def _role_match(rv: Optional[str]) -> bool:
            if not rv:
                return False
            rv = rv.lower()
            if role_norm == "both":
                return rv == "both"
            if role_norm == "expo":
                return rv in {"expo", "both"}
            if role_norm == "forum":
                return rv in {"forum", "both"}
            return False

        rows = [r for r in rows if _role_match(r.get("role"))]

    if q:
        ql = q.lower().strip()
        rows = [r for r in rows if (r.get("name") or "").lower().find(ql) >= 0]

    if not latest_first:
        rows = list(reversed(rows))

    rows = rows[offset:offset + limit]

    out: list[dict] = []
    for r in rows:
        logo = r.get("logo") or r.get("logo_url") or r.get("photo")
        out.append({
            "id": r.get("id"),
            "name": r.get("name") or "",
            "role": r.get("role"),
            "bio": r.get("bio") or "",
            "logo_url": _resolve_logo_url(logo),
            "images": [],
        })
    print(f"[participants] list -> {len(out)} items")
    return out


# ---------------- DETAIL PAGE ---------------- #
async def get_participant(
    req: Request,
    *,
    participant_id: int,
) -> Optional[dict]:
    raw = await api_get(req, f"/participants/{participant_id}")
    r = _unwrap_object(raw)
    if not r:
        return None

    bio = r.get("bio") or ""
    intro_html = _first_paragraph_html(bio)
    body_html = md_to_html(bio)

    images_in = r.get("images") or []
    # backend often returns [{"id":..., "path":"..."}]; support other shapes, too
    if images_in and isinstance(images_in, list) and isinstance(images_in[0], dict) and "path" in images_in[0]:
        all_images = _resolve_image_list([{"path": it.get("path")} for it in images_in])
    else:
        all_images = _resolve_image_list(images_in)

    images_hero = all_images[:3]
    images_rest = all_images[3:]

    logo = r.get("logo") or r.get("logo_url") or r.get("photo")
    return {
        "id": r.get("id"),
        "name": r.get("name") or "",
        "role": r.get("role"),
        "bio": bio,
        "intro_html": intro_html,
        "body_html": body_html,
        "logo_url": _resolve_logo_url(logo),
        "images_hero": images_hero,
        "images_rest": images_rest,
        "created_at": r.get("created_at"),
        "updated_at": r.get("updated_at"),
    }
