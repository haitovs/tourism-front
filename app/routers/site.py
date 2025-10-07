# app/routers/site.py
from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse

from app.services import expo_sectors as sectors_srv
from app.services import news as news_srv
from app.services import speakers as speakers_srv
from app.services import sponsors as sponsor_srv
from app.services import statistics as stats_srv

from ..core.settings import settings
from ..core.templates import templates

router = APIRouter()


def _resolve_lang(req: Request) -> str:
    lang = req.query_params.get("lang") or req.cookies.get("lang") or settings.DEFAULT_LANG
    return lang if lang in settings.SUPPORTED_LANGS else settings.DEFAULT_LANG


@router.get("/", response_class=HTMLResponse)
async def home(req: Request):
    lang = _resolve_lang(req)

    ctx = {
        "request": req,
        "lang": lang,
        "settings": settings,
        "sponsors_top": sponsor_srv.get_top_sponsors(lang=lang),
        "gold": sponsor_srv.list_all_sponsors_by_tier(tier="gold", lang=lang),
        "silver": sponsor_srv.list_all_sponsors_by_tier(tier="silver", lang=lang),
        "bronze": sponsor_srv.list_all_sponsors_by_tier(tier="bronze", lang=lang),
        "sectors": sectors_srv.list_home_sectors(limit=3, latest_first=True),
        "stats": stats_srv.get_statistics(),
        "speakers": speakers_srv.get_featured_speakers(limit=3),
        "news": news_srv.get_latest_news(limit=5),
    }
    resp = templates.TemplateResponse("index.html", ctx)
    resp.set_cookie("lang", lang, max_age=60 * 60 * 24 * 365, httponly=False, samesite="lax")
    return resp
