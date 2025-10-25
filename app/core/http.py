# app/core/http.py
from __future__ import annotations

from typing import Any, Dict, Optional

import httpx
from fastapi import Request

from app.core.settings import settings


def _debug_preview(data: Any, max_len: int = 400) -> str:
    try:
        s = str(data)
        return (s[:max_len] + "…") if len(s) > max_len else s
    except Exception:
        return "<non-printable>"


def abs_media(path: str | None) -> str:
    if not path:
        return ""
    p = path.strip()
    low = p.lower()
    if low.startswith("http://") or low.startswith("https://"):
        return p

    base = settings.MEDIA_BASE_URL.rstrip("/")
    pref = settings.MEDIA_PREFIX.strip("/")

    p_no_lead = p.lstrip("/")
    if pref and p_no_lead.startswith(pref + "/"):
        return f"{base}/{p_no_lead}"

    if p.startswith("/"):
        return f"{base}/{p_no_lead}"

    return f"{base}/{pref}/{p_no_lead}" if pref else f"{base}/{p_no_lead}"


def _current_lang(req: Request) -> str:
    return getattr(getattr(req, "state", None), "lang", settings.DEFAULT_LANG)


def _current_site_id(req: Request):
    site = getattr(req.state, "site", None)
    sid = getattr(site, "id", None)
    if sid is None:
        sid = getattr(settings, "DEFAULT_TENANT_ID", None)
    return sid


async def api_get(req: Request, path: str, params=None):
    params = dict(params or {})
    params.setdefault("lang", _current_lang(req))

    headers = {}
    headers["Accept-Language"] = _current_lang(req)

    sid = _current_site_id(req)
    if sid is not None:
        params.setdefault("site_id", sid)
        headers["X-Site-Id"] = str(sid)

    slug = req.cookies.get("admin_site_slug") or req.cookies.get("site") or None
    if slug:
        params.setdefault("site", slug)
        headers["X-Site-Slug"] = slug

    url = settings.BACKEND_BASE_URL.rstrip("/") + "/" + path.lstrip("/")

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        r = await client.get(url, params=params, headers=headers)
        r.raise_for_status()
        data = r.json()
        try:
            if isinstance(data, list):
                print(f"[HTTP] GET {r.url} -> list: {len(data)}")
            else:
                print(f"[HTTP] GET {r.url} -> type={type(data).__name__}")
        except Exception:
            pass
        return data


async def api_post(req: Request, path: str, data: Optional[Dict[str, Any]] = None, files=None) -> Any:
    url = settings.BACKEND_BASE_URL.rstrip("/") + "/" + path.lstrip("/")
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        r = await client.post(url, data=data, files=files)
        r.raise_for_status()
        out = r.json()
        print(f"[HTTP] POST {r.url} -> {type(out).__name__}: {_debug_preview(out)}")
        return out
