# app/routers/agenda_router.py
from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse

from app.routers.site import _resolve_site_id
from app.services import agenda as agenda_srv
from app.services.text_utils import normalize_textblock, split_short_and_topic

from ..core.settings import settings
from ..core.templates import templates

router = APIRouter()


@router.get("/agenda", response_class=HTMLResponse)
async def agenda_page(req: Request):
    lang = getattr(req.state, "lang", settings.DEFAULT_LANG)
    site_id = _resolve_site_id(req)

    days = agenda_srv.list_days_with_episodes(site_id=site_id)

    selected_day_id = None
    if days:
        selected_day_id = days[0]["id"]

    for day in days:
        episodes = day.get("episodes", []) or []
        for ep in episodes:
            short, topic = split_short_and_topic(ep.get("description_md") or "")
            ep["short_desc"] = short
            ep["topic_desc"] = topic

            moderators = ep.get("moderators") or []
            if moderators:
                mod0 = moderators[0]
                mod0["description_norm"] = normalize_textblock(mod0.get("description") or "")

            sponsors = ep.get("sponsors") or []
            ep["top_sponsor"] = sponsors[0] if sponsors else None

    ctx = {
        "request": req,
        "lang": lang,
        "settings": settings,
        "days": days,
        "selected_day_id": selected_day_id,
    }
    return templates.TemplateResponse("agenda.html", ctx)
