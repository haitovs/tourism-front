# app/routers/about_forum_router.py
from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse

from ..core.settings import settings
from ..core.templates import templates

router = APIRouter()


@router.get("/about-the-forum", response_class=HTMLResponse)
async def about_forum(req: Request):
    lang = getattr(req.state, "lang", settings.DEFAULT_LANG)
    ctx = {"request": req, "lang": lang, "settings": settings}
    return templates.TemplateResponse("about_forum.html", ctx)
