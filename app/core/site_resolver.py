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
    # "host:slug:id,..."
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
        site_map = _parse_site_map(settings.SITE_MAP_RAW)

        slug, sid = None, None
        if host in site_map:
            slug, sid = site_map[host]
        else:
            # fallback to Stage 2 envs
            slug = getattr(settings, "FRONT_SITE_SLUG", None)
            sid = getattr(settings, "FRONT_SITE_ID", None)

        request.state.site = SiteInfo(id=sid, slug=slug, host=host)
        return await call_next(request)
