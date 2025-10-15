# app/routers/about_expo_router.py
from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse

from app.routers.site import _resolve_lang

from ..core.settings import settings
from ..core.templates import templates

router = APIRouter()


@router.get("/about-the-expo", response_class=HTMLResponse)
async def about_expo(req: Request):
    lang = _resolve_lang(req)
    ctx = {"request": req, "lang": lang, "settings": settings}
    return templates.TemplateResponse("about_expo.html", ctx)
