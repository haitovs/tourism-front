# app/routers/faq_router.py
from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse

from app.core.settings import settings
from app.core.templates import templates
from app.services import faqs as faq_srv

router = APIRouter()


@router.get("/faq", response_class=HTMLResponse)
async def faq_page(req: Request):
    lang = getattr(req.state, "lang", settings.DEFAULT_LANG)
    items = await faq_srv.list_faqs(req, limit=None)
    ctx = {"request": req, "lang": lang, "settings": settings, "faqs": items or []}
    return templates.TemplateResponse("faq.html", ctx)
