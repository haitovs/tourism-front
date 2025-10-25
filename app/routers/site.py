# app/routers/site.py
from asyncio import gather

from fastapi import APIRouter, Request, Response
from starlette.responses import HTMLResponse

from app.core.language_middleware import LANG_COOKIE
from app.services import expo_sectors as sectors_srv
from app.services import faqs as faq_srv
from app.services import news as news_srv
from app.services import organizers as org_srv
from app.services import participants as participants_srv
from app.services import partners as partners_srv
from app.services import speakers as speakers_srv
from app.services import sponsors as sponsor_srv
from app.services import statistics as stats_srv
from app.services import timer as timer_srv

from ..core.settings import settings
from ..core.templates import templates

router = APIRouter()


def _resolve_site_id(req: Request) -> int | None:
    site = getattr(req.state, "site", None)
    return getattr(site, "id", None) if site else None


@router.post("/set-lang/{code}")
def set_lang(code: str, response: Response):
    code = (code or "").lower().split("-")[0]
    if code not in settings.SUPPORTED_LANGS:
        code = settings.DEFAULT_LANG
    response.set_cookie(LANG_COOKIE, code, max_age=60 * 60 * 24 * 365, samesite="lax")
    return {"ok": True, "lang": code}


@router.get("/", response_class=HTMLResponse)
async def home(req: Request):
    lang = getattr(req.state, "lang", settings.DEFAULT_LANG)
    site_id = _resolve_site_id(req)

    # timer (sync)
    deadline_dt = timer_srv.get_deadline_from_settings(settings)
    timer_ctx = timer_srv.build_timer_context(deadline_dt)

    # fetch async data in parallel
    sectors_task = sectors_srv.list_home_sectors(req, limit=3, latest_first=True)
    news_task = news_srv.get_latest_news(req, limit=5)
    faqs_task = faq_srv.list_faqs(req, limit=5)
    speakers_task = speakers_srv.get_featured_speakers(req, limit=3)
    organizers_task = org_srv.list_organizers(req, limit=None)
    partners_task = partners_srv.list_partners(req, limit=None)
    participants12_task = participants_srv.list_participants(req, limit=12, latest_first=True)
    participants_expo_task = participants_srv.list_participants(req, limit=8, role="expo")
    participants_forum_task = participants_srv.list_participants(req, limit=8, role="forum")
    participants_both_task = participants_srv.list_participants(req, limit=8, role="both")

    (
        sectors,
        news,
        faqs,
        speakers,
        organizers,
        partners,
        participants12,
        participants_expo,
        participants_forum,
        participants_both,
    ) = await gather(
        sectors_task,
        news_task,
        faqs_task,
        speakers_task,
        organizers_task,
        partners_task,
        participants12_task,
        participants_expo_task,
        participants_forum_task,
        participants_both_task,
    )

    ctx = {
        "request": req,
        "lang": lang,
        "settings": settings,

        # sponsors/statistics (sync)
        "sponsors_top": sponsor_srv.get_top_sponsors(lang=lang, site_id=site_id),
        "sponsors_top_flat": sponsor_srv.get_top_sponsors_flat(lang=lang, site_id=site_id, max_items=5),
        "sponsors_top_view": sponsor_srv.build_top_sponsors_view(lang=lang, site_id=site_id, max_items=5),
        "gold": sponsor_srv.list_all_sponsors_by_tier(tier="gold", lang=lang, site_id=site_id),
        "silver": sponsor_srv.list_all_sponsors_by_tier(tier="silver", lang=lang, site_id=site_id),
        "bronze": sponsor_srv.list_all_sponsors_by_tier(tier="bronze", lang=lang, site_id=site_id),
        "stats": stats_srv.get_statistics(site_id=site_id),

        # async results
        "sectors": sectors or [],
        "news": news or [],
        "faqs": faqs or [],
        "speakers": speakers or [],

        # organizers
        "organizers": organizers or [],
        "organizers_data": {
            "items": organizers or []
        },

        # partners
        "partners": partners or [],
        "partners_data": {
            "items": partners or []
        },

        # participants
        "participants": participants12 or [],
        "participants_expo": participants_expo or [],
        "participants_forum": participants_forum or [],
        "participants_both": participants_both or [],

        # timer
        "timer": timer_ctx,
    }

    return templates.TemplateResponse("index.html", ctx)
