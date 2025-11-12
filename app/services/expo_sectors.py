from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Optional
from urllib.parse import urljoin

import markdown as _md_lib
from fastapi import Request

from app.core.http import api_get
from app.core.settings import settings
from app.utils.timed_cache import TimedCache

_bullet_like = re.compile(r"(\S)\s-\s+")
_LIST_CACHE = TimedCache(ttl_seconds=20.0)
_DETAIL_CACHE = TimedCache(ttl_seconds=30.0)


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
    # honor MEDIA_PREFIX if present
    if url.startswith("/"):
        return urljoin(base, url.lstrip("/"))
    pref = settings.MEDIA_PREFIX.strip("/")
    if pref:
        return urljoin(base, f"{pref}/{url.lstrip('/')}")
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
    # Backend: [{id, path}]
    if isinstance(items, list) and items and isinstance(items[0], dict) and "path" in items[0]:
        return [_resolve_media(x.get("path")) for x in items if isinstance(x, dict) and x.get("path")]
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


async def list_home_sectors(
    req: Request,
    limit: int = 3,
    latest_first: bool = True,
    site_id: Optional[int] = None,
) -> list[dict]:
    import asyncio
    import logging

    import httpx
    log = logging.getLogger("services.expo_sectors")

    cache_key = f"sectors:{_site_cache_key(req)}:{limit}:{latest_first}:{site_id}"
    cached = _LIST_CACHE.get(cache_key)
    if cached is not None:
        return cached

    items = None
    for attempt in range(2):  # 1 try + 1 retry
        try:
            items = await api_get(req, "/expo-sectors/")
            break
        except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
            log.warning("list_home_sectors timeout (attempt %d/2): %s", attempt + 1, e)
            if attempt == 0:
                await asyncio.sleep(0.35)
                continue
        except httpx.HTTPError as e:
            log.error("list_home_sectors HTTP error: %r", e)
            break
        except Exception as e:
            log.exception("list_home_sectors unexpected: %r", e)
            break

    items = items or []

    if latest_first:
        try:
            items = sorted(items, key=lambda x: int(x.get("id", 0)), reverse=True)
        except Exception:
            pass

    items = items[:limit]
    projected = [{
        "id": it.get("id"),
        "header": it.get("header") or "",
        "description": it.get("description") or "",
        "logo_url": _resolve_logo_url(it.get("logo")),
    } for it in items]
    _LIST_CACHE.set(cache_key, projected)
    return projected


async def get_sector(req: Request, sector_id: int, site_id: Optional[int] = None) -> Optional[dict]:
    import asyncio
    import logging

    import httpx
    log = logging.getLogger("services.expo_sectors")

    cache_key = f"sector:{_site_cache_key(req)}:{sector_id}:{site_id}"
    cached = _DETAIL_CACHE.get(cache_key)
    if cached is not None:
        return cached

    it = None
    for attempt in range(2):
        try:
            it = await api_get(req, f"/expo-sectors/{sector_id}")
            break
        except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
            log.warning("get_sector[%s] timeout (attempt %d/2): %s", sector_id, attempt + 1, e)
            if attempt == 0:
                await asyncio.sleep(0.35)
                continue
        except httpx.HTTPError as e:
            log.error("get_sector[%s] HTTP error: %r", sector_id, e)
            return None
        except Exception as e:
            log.exception("get_sector[%s] unexpected: %r", sector_id, e)
            return None

    if not it:
        return None

    header = it.get("header")
    description = it.get("description")
    extended_md = it.get("extended_description")

    intro_html = _first_paragraph_html(description)
    body_html = md_to_html(extended_md or "")

    all_images = _resolve_image_list((it.get("images") or []))
    images_hero = all_images[:3]
    images_rest = all_images[3:]

    result = {
        "id": it.get("id"),
        "header": header,
        "subtitle": None,
        "description": description,
        "logo_url": _resolve_logo_url(it.get("logo")),
        "hero_url": None,
        "tagline": None,
        "intro_html": intro_html,
        "body_html": body_html,
        "images_hero": images_hero,
        "images_rest": images_rest,
        "points_left": None,
        "points_right": None,
    }
    _DETAIL_CACHE.set(cache_key, result)
    return result
def _site_cache_key(req: Request | None) -> str:
    if req is None:
        return "0"
    site = getattr(getattr(req, "state", None), "site", None)
    sid = getattr(site, "id", None) or getattr(settings, "FRONT_SITE_ID", 0)
    slug = getattr(site, "slug", None) or getattr(settings, "FRONT_SITE_SLUG", "")
    lang = getattr(getattr(req, "state", None), "lang", settings.DEFAULT_LANG)
    return f"{sid}:{slug}:{lang}"
