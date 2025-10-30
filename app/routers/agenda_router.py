# app/routers/agenda_router.py
from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse

from app.routers.site import _resolve_site_id
from app.services import episodes as episodes_srv
from app.services.text_utils import normalize_textblock, split_short_and_topic

from ..core.settings import settings
from ..core.templates import templates, themed_name

router = APIRouter()


@router.get("/agenda", response_class=HTMLResponse)
async def agenda_page(req: Request):
    lang = getattr(req.state, "lang", settings.DEFAULT_LANG)
    site_id = _resolve_site_id(req)

    days = await episodes_srv.list_days_with_episode_views(req, site_id=site_id)

    selected_day_id = None
    if days:
        selected_day_id = days[0]["id"]

    for day in days:
        for ep in (day.get("episodes") or []):
            short, topic = split_short_and_topic(ep.get("description_md") or "")
            ep["short_desc"] = short
            ep["topic_desc"] = topic
            if ep.get("moderators"):
                ep["moderators"][0]["description_norm"] = normalize_textblock(ep["moderators"][0].get("description") or "")

            sponsors = ep.get("sponsors") or []
            ep["top_sponsor"] = sponsors[0] if sponsors else None

    ctx = {
        "request": req,
        "lang": lang,
        "settings": settings,
        "days": days,
        "selected_day_id": selected_day_id,
    }
    template_name = themed_name(req, "agenda.html")
    return templates.TemplateResponse(template_name, ctx)
