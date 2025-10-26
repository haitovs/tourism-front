# app/routers/site.py
from asyncio import gather

from fastapi import APIRouter, Request, Response
from starlette.responses import HTMLResponse, RedirectResponse

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
def set_lang(code: str, request: Request, response: Response):
    code = (code or "").lower().split("-")[0]
    if code not in settings.SUPPORTED_LANGS:
        code = settings.DEFAULT_LANG
    response.set_cookie(LANG_COOKIE, code, max_age=60 * 60 * 24 * 365, samesite="lax")
    referer = request.headers.get("referer") or "/"
    return RedirectResponse(referer, status_code=303)


@router.get("/", response_class=HTMLResponse)
async def home(req: Request):
    import logging
    from asyncio import create_task, gather
    log = logging.getLogger("routers.site.home")

    lang = getattr(req.state, "lang", settings.DEFAULT_LANG)
    site_id = _resolve_site_id(req)

    # timer (sync)
    deadline_dt = timer_srv.get_deadline_from_settings(settings)
    timer_ctx = timer_srv.build_timer_context(deadline_dt)

    # fetch async data in parallel
    # NOTE: we fetch participants ONCE and derive the four lists locally.
    sectors_task = create_task(sectors_srv.list_home_sectors(req, limit=3, latest_first=True))
    news_task = create_task(news_srv.get_latest_news(req, limit=5))
    faqs_task = create_task(faq_srv.list_faqs(req, limit=5))
    speakers_task = create_task(speakers_srv.get_featured_speakers(req, limit=3))
    organizers_task = create_task(org_srv.list_organizers(req, limit=None))
    partners_task = create_task(partners_srv.list_partners(req, limit=None))
    participants_all_task = create_task(participants_srv.list_participants(req, limit=200, latest_first=True))

    # Defensive gather: never raise, we’ll default to [] on exceptions
    results = await gather(
        sectors_task,
        news_task,
        faqs_task,
        speakers_task,
        organizers_task,
        partners_task,
        participants_all_task,
        return_exceptions=True,
    )

    def _ok(idx):
        val = results[idx]
        if isinstance(val, Exception):
            log.warning("home(): task %d failed: %r", idx, val)
            return []
        return val or []

    sectors = _ok(0)
    news = _ok(1)
    faqs = _ok(2)
    speakers = _ok(3)
    organizers = _ok(4)
    partners = _ok(5)
    participants_all = _ok(6)

    # Derive participants slices locally (keeps one backend call)
    participants12 = participants_all[:12]
    participants_expo = [p for p in participants_all if (p.get("role") in {"expo", "both"})][:8]
    participants_forum = [p for p in participants_all if (p.get("role") in {"forum", "both"})][:8]
    participants_both = [p for p in participants_all if p.get("role") == "both"][:8]

    # sponsors/statistics (sync; services already hardened)
    sponsors_top = sponsor_srv.get_top_sponsors(lang=lang, site_id=site_id)
    sponsors_top_flat = sponsor_srv.get_top_sponsors_flat(lang=lang, site_id=site_id, max_items=5)
    sponsors_top_view = sponsor_srv.build_top_sponsors_view(lang=lang, site_id=site_id, max_items=5)
    gold = sponsor_srv.list_all_sponsors_by_tier(tier="gold", lang=lang, site_id=site_id)
    silver = sponsor_srv.list_all_sponsors_by_tier(tier="silver", lang=lang, site_id=site_id)
    bronze = sponsor_srv.list_all_sponsors_by_tier(tier="bronze", lang=lang, site_id=site_id)
    stats = stats_srv.get_statistics(site_id=site_id)

    ctx = {
        "request": req,
        "lang": lang,
        "settings": settings,

        # sponsors/statistics (sync)
        "sponsors_top": sponsors_top,
        "sponsors_top_flat": sponsors_top_flat,
        "sponsors_top_view": sponsors_top_view,
        "gold": gold,
        "silver": silver,
        "bronze": bronze,
        "stats": stats,

        # async results
        "sectors": sectors,
        "news": news,
        "faqs": faqs,
        "speakers": speakers,

        # organizers
        "organizers": organizers,
        "organizers_data": {
            "items": organizers
        },

        # partners
        "partners": partners,
        "partners_data": {
            "items": partners
        },

        # participants (derived locally)
        "participants": participants12,
        "participants_expo": participants_expo,
        "participants_forum": participants_forum,
        "participants_both": participants_both,

        # timer
        "timer": timer_ctx,
    }

    return templates.TemplateResponse("index.html", ctx)
