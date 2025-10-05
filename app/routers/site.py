# app/routers/site.py
from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse

from app.services import sponsors as sponsor_srv

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
        "sponsors_top": sponsor_srv.get_top_sponsors(lang=lang),
        "gold": sponsor_srv.list_sponsors_by_tier(tier="gold", page=1, per_page=10, lang=lang),
        "silver": sponsor_srv.list_sponsors_by_tier(tier="silver", page=1, per_page=10, lang=lang),
        "bronze": sponsor_srv.list_sponsors_by_tier(tier="bronze", page=1, per_page=10, lang=lang),
    }
    resp = templates.TemplateResponse("index.html", ctx)
    resp.set_cookie("lang", lang, max_age=60 * 60 * 24 * 365, httponly=False, samesite="lax")
    return resp
