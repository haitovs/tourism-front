# app/routers/site.py
from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse

from app.services import expo_sectors as sectors_srv
from app.services import faqs as faq_srv
from app.services import news as news_srv
from app.services import organizers as org_srv
from app.services import participants as participants_srv
from app.services import partners as partners_srv
from app.services import speakers as speakers_srv
from app.services import sponsors as sponsor_srv
from app.services import statistics as stats_srv

from ..core.settings import settings
from ..core.templates import templates

router = APIRouter()


def _resolve_lang(req: Request) -> str:
    lang = req.query_params.get("lang") or req.cookies.get("lang") or settings.DEFAULT_LANG
    return lang if lang in settings.SUPPORTED_LANGS else settings.DEFAULT_LANG


def _resolve_site_id(req: Request) -> int | None:
    site = getattr(req.state, "site", None)
    return getattr(site, "id", None) if site else None


@router.get("/", response_class=HTMLResponse)
async def home(req: Request):
    lang = _resolve_lang(req)
    site_id = _resolve_site_id(req)

    ctx = {
        "request": req,
        "lang": lang,
        "settings": settings,

        # TOP sponsors (grouped + flat kept for backward-compat) + new view-model
        "sponsors_top": sponsor_srv.get_top_sponsors(lang=lang, site_id=site_id),
        "sponsors_top_flat": sponsor_srv.get_top_sponsors_flat(lang=lang, site_id=site_id, max_items=5),
        "sponsors_top_view": sponsor_srv.build_top_sponsors_view(lang=lang, site_id=site_id, max_items=5),

        # LIST tiers (tenant-scoped)
        "gold": sponsor_srv.list_all_sponsors_by_tier(tier="gold", lang=lang, site_id=site_id),
        "silver": sponsor_srv.list_all_sponsors_by_tier(tier="silver", lang=lang, site_id=site_id),
        "bronze": sponsor_srv.list_all_sponsors_by_tier(tier="bronze", lang=lang, site_id=site_id),
        "sectors": sectors_srv.list_home_sectors(limit=3, latest_first=True),
        "stats": stats_srv.get_statistics(),
        "speakers": speakers_srv.get_featured_speakers(limit=3, site_id=site_id),
        "news": news_srv.get_latest_news(limit=5),
        "faqs": faq_srv.list_faqs(limit=5),
        "organizers": org_srv.list_organizers(),
        "organizers_data": {
            "items": org_srv.list_organizers()
        },
        "partners": partners_srv.list_partners(),

        # ✅ fixed typo here
        "participants": participants_srv.list_participants(limit=12, latest_first=True, site_id=site_id),
        "participants_expo": participants_srv.list_participants(limit=8, role="expo", site_id=site_id),
        "participants_forum": participants_srv.list_participants(limit=8, role="forum", site_id=site_id),
        "participants_both": participants_srv.list_participants(limit=8, role="both", site_id=site_id),
    }

    resp = templates.TemplateResponse("index.html", ctx)
    resp.set_cookie("lang", lang, max_age=60 * 60 * 24 * 365, httponly=False, samesite="lax")
    return resp
