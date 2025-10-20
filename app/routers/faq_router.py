# app/routers/faq_router.py
from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse

from app.core.settings import settings
from app.core.templates import templates
from app.routers.site import _resolve_site_id
from app.services import faqs as faq_srv

router = APIRouter()


@router.get("/faq", response_class=HTMLResponse)
async def faq_page(req: Request):
    lang = getattr(req.state, "lang", settings.DEFAULT_LANG)
    site_id = _resolve_site_id(req)
    items = faq_srv.list_faqs(site_id=site_id, limit=None)
    ctx = {"request": req, "lang": lang, "settings": settings, "faqs": items}
    return templates.TemplateResponse("faq.html", ctx)
