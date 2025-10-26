# app/core/http.py
from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

import httpx
from fastapi import Request

from app.core.settings import settings

log = logging.getLogger("app.http")
_fallback_client: Optional[httpx.AsyncClient] = None


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


def _get_client(req: Request) -> httpx.AsyncClient:
    client = getattr(getattr(req, "app", None), "state", None)
    client = getattr(client, "http", None)
    if isinstance(client, httpx.AsyncClient):
        return client

    global _fallback_client
    if _fallback_client is None:
        _fallback_client = httpx.AsyncClient(
            timeout=httpx.Timeout(12.0, connect=2.0, read=12.0, write=12.0, pool=12.0),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            follow_redirects=True,
            http2=True,
        )
    return _fallback_client


async def api_get(req: Request, path: str, params=None):
    params = dict(params or {})
    params.setdefault("lang", _current_lang(req))

    headers: Dict[str, str] = {
        "Accept": "application/json",
        "Accept-Language": _current_lang(req),
        "Connection": "keep-alive",
    }

    sid = _current_site_id(req)
    if sid is not None:
        params.setdefault("site_id", sid)
        headers["X-Site-Id"] = str(sid)

    slug = req.cookies.get("admin_site_slug") or req.cookies.get("site") or None
    if slug:
        params.setdefault("site", slug)
        headers["X-Site-Slug"] = slug

    if settings.BACKEND_HOST_HEADER:
        headers["Host"] = settings.BACKEND_HOST_HEADER

    url = settings.BACKEND_BASE_URL.rstrip("/") + "/" + path.lstrip("/")

    client = _get_client(req)
    t0 = time.perf_counter()
    try:
        r = await client.get(url, params=params, headers=headers)
        r.raise_for_status()

        if "application/json" in (r.headers.get("content-type") or ""):
            data = r.json()
        else:
            data = r.text
        try:
            kind = f"list:{len(data)}" if isinstance(data, list) else f"type={type(data).__name__}"
            log.debug("[HTTP] GET %s -> %s (status=%s, %dB)", str(r.url), kind, r.status_code, len(r.content))
        except Exception:
            pass
        return data
    except httpx.HTTPError as e:
        body_preview = ""
        try:
            resp = getattr(e, "response", None)
            if resp is not None:
                body_preview = _debug_preview(resp.text)
        except Exception:
            pass
        log.error("[HTTP] GET %s failed: %s | %s", url, repr(e), body_preview)
        raise
    finally:
        dt = (time.perf_counter() - t0) * 1000
        log.info("[HTTP] GET %s in %.1f ms", url, dt)


async def api_post(req: Request, path: str, data: Optional[Dict[str, Any]] = None, files=None) -> Any:
    """
    POST with pooled client, lang/site propagation for headers, robust timeout, and concise logging.
    Matches original semantics (form 'data' + optional 'files').
    """
    headers: Dict[str, str] = {
        "Accept": "application/json",
        "Accept-Language": _current_lang(req),
        "Connection": "keep-alive",
    }

    sid = _current_site_id(req)
    if sid is not None:
        headers["X-Site-Id"] = str(sid)

    slug = req.cookies.get("admin_site_slug") or req.cookies.get("site") or None
    if slug:
        headers["X-Site-Slug"] = slug

    if settings.BACKEND_HOST_HEADER:
        headers["Host"] = settings.BACKEND_HOST_HEADER

    url = settings.BACKEND_BASE_URL.rstrip("/") + "/" + path.lstrip("/")

    client = _get_client(req)
    t0 = time.perf_counter()
    try:
        # Preserve original behavior: send as form data unless files are present.
        r = await client.post(url, data=data, files=files, headers=headers)
        r.raise_for_status()
        out = r.json() if "application/json" in (r.headers.get("content-type") or "") else r.text
        log.debug("[HTTP] POST %s -> %s: %s", str(r.url), type(out).__name__, _debug_preview(out))
        return out
    except httpx.HTTPError as e:
        body_preview = ""
        try:
            resp = getattr(e, "response", None)
            if resp is not None:
                body_preview = _debug_preview(resp.text)
        except Exception:
            pass
        log.error("[HTTP] POST %s failed: %s | %s", url, repr(e), body_preview)
        raise
    finally:
        dt = (time.perf_counter() - t0) * 1000
        log.info("[HTTP] POST %s in %.1f ms", url, dt)
