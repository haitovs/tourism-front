# app/routers/htmx.py
from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse

from app.services import sponsors as sponsor_srv

from ..core.settings import settings
from ..core.templates import templates

router = APIRouter(prefix="/x")


def _lang(req: Request) -> str:
    l = req.query_params.get("lang") or req.cookies.get("lang") or settings.DEFAULT_LANG
    return l if l in settings.SUPPORTED_LANGS else settings.DEFAULT_LANG


@router.get("/sponsors/top", response_class=HTMLResponse)
async def sponsors_top(req: Request):
    lang = _lang(req)
    data = sponsor_srv.get_top_sponsors(lang=lang)
    return templates.TemplateResponse("_sponsors_top.html", {"request": req, "data": data, "lang": lang})


@router.get("/sponsors/{tier}", response_class=HTMLResponse)
async def sponsors_tier(req: Request, tier: str, page: int = 1):
    lang = _lang(req)
    tier = tier.lower()
    if tier not in {"gold", "silver", "bronze"}:
        return HTMLResponse("", status_code=204)
    data = sponsor_srv.list_sponsors_by_tier(tier=tier, page=page, per_page=4, lang=lang)
    return templates.TemplateResponse("_sponsors_carousel.html", {"request": req, "data": data, "lang": lang})
