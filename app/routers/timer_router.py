# app/routers/timer.py  (FRONT APP)
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Query, Request

from app.core.settings import settings
from app.services.timer import build_timer_context, get_deadline_from_settings

router = APIRouter(prefix="/timer", tags=["Timer"])


@router.get("/active")
async def get_active_timer(
        request: Request,
        site: str | None = Query(None),
        site_id: int | None = Query(None),
):
    client: httpx.AsyncClient = request.app.state.http

    # ✅ Auto-detect current site slug from SiteResolverMiddleware
    resolved_slug = getattr(getattr(request.state, "site", None), "slug", None) or None
    if not site and site_id is None and resolved_slug:
        site = resolved_slug

    # Fallback to configured default site (main theme) if nothing resolved
    if not site and site_id is None:
        default_site_id = getattr(settings, "FRONT_SITE_ID", None)
        if default_site_id:
            try:
                candidate_id = int(default_site_id)
                if candidate_id > 0:
                    site_id = candidate_id
            except (TypeError, ValueError):
                site_id = None
        if site_id is None and not site:
            default_slug = getattr(settings, "FRONT_SITE_SLUG", None) or None
            if default_slug:
                site = default_slug

    params = {}
    if site_id is not None:
        params["site_id"] = site_id
    elif site:
        params["site"] = site

    headers = {}
    # also forward as a header, in case backend reads X-Site-Slug
    if site and not request.headers.get("X-Site-Slug"):
        headers["X-Site-Slug"] = site

    url = settings.BACKEND_BASE_URL.rstrip("/") + "/timer/active"

    try:
        resp = await client.get(url, params=params, headers=headers, timeout=5.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass

    # Fallback so UI still renders
    now = datetime.now(timezone.utc)
    deadline_dt = get_deadline_from_settings(settings)
    return {
        "id": None,
        "event_name": getattr(settings, "DEFAULT_EVENT_NAME", "Event"),
        "start_time": None,
        "end_time": deadline_dt.astimezone(timezone.utc).isoformat(),
        "is_active": True,
        "mode": "UNTIL_END",
        "created_at": None,
        "updated_at": None,
        "server_time": now.isoformat(),
        "site_id": None,
        "site": site or None,
    }


@router.get("/api/timer")
def front_deadline_fallback():
    now = datetime.now(timezone.utc)
    deadline = get_deadline_from_settings(settings)
    ctx = build_timer_context(deadline)  # returns deadline_iso_utc, deadline_month_upper, deadline_day
    return {
        "event_name": getattr(settings, "DEFAULT_EVENT_NAME", "Event"),
        **ctx,
        "server_time": now.isoformat(),
    }
