# app/core/site_resolver.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.settings import settings


@dataclass
class SiteInfo:
    id: Optional[int]
    slug: Optional[str]
    host: Optional[str]


def _parse_site_map(raw: str) -> dict[str, Tuple[str, int]]:
    out: dict[str, Tuple[str, int]] = {}
    for item in (raw or "").split(","):
        item = item.strip()
        if not item:
            continue
        try:
            host, slug, sid = item.split(":")
            host = host.strip().lower()
            slug = slug.strip()
            sid = int(sid.strip())
            if host and slug and sid > 0:
                out[host] = (slug, sid)
        except Exception:
            continue
    return out


_SITE_MAP_CACHE: tuple[str, dict[str, Tuple[str, int]]] = ("", {})


def _current_site_map() -> dict[str, Tuple[str, int]]:
    raw = settings.SITE_MAP_RAW or ""
    cached_raw, cached_map = _SITE_MAP_CACHE
    if raw == cached_raw and cached_map:
        return cached_map
    parsed = _parse_site_map(raw)
    globals()["_SITE_MAP_CACHE"] = (raw, parsed)
    return parsed


def _request_host(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-host") or request.headers.get("forwarded")
    if fwd and "host=" in fwd.lower():
        # Forwarded: host=example.com;proto=https
        try:
            parts = fwd.split(";")
            for p in parts:
                if "host=" in p.lower():
                    return p.split("=", 1)[1].strip().split(",")[0].split(":")[0].lower()
        except Exception:
            pass
    if request.headers.get("x-forwarded-host"):
        return request.headers["x-forwarded-host"].split(",")[0].split(":")[0].lower()
    h = (request.headers.get("host") or "").split(":")[0].strip().lower()
    return h


class SiteResolverMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        host = _request_host(request)
        site_map = _current_site_map()

        slug, sid = None, None
        if host in site_map:
            slug, sid = site_map[host]

        if settings.ALLOW_SITE_OVERRIDE and request.method == "GET":
            qp = request.query_params
            override_slug = qp.get("__site") or request.headers.get("x-site-slug")
            override_id = qp.get("__site_id") or request.headers.get("x-site-id")
            if override_slug:
                override_slug = override_slug.strip()
                if override_slug:
                    slug = override_slug
                    if not sid:
                        for _host, (s_slug, s_id) in site_map.items():
                            if s_slug == slug:
                                sid = s_id
                                break
            if override_id:
                try:
                    sid_val = int(str(override_id).strip())
                    if sid_val > 0:
                        sid = sid_val
                except Exception:
                    pass

        request.state.site = SiteInfo(id=sid, slug=slug, host=host)
        return await call_next(request)
