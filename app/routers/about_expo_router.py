# app/routers/about_expo_router.py
from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse

from ..core.settings import settings
from ..core.templates import templates, themed_name

router = APIRouter()


@router.get("/about-the-expo", response_class=HTMLResponse)
async def about_expo(req: Request):
    lang = getattr(req.state, "lang", settings.DEFAULT_LANG)
    ctx = {"request": req, "lang": lang, "settings": settings}
    template_name = themed_name(req, "about_expo.html")
    return templates.TemplateResponse(template_name, ctx)
