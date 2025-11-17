# app/routers/terms_router.py
import logging

from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse

from app.routers.site import _resolve_site_id
from app.services import terms as legal_srv

from ..core.settings import settings
from ..core.templates import templates, themed_name

router = APIRouter()


@router.get("/terms", response_class=HTMLResponse)
async def terms_of_use_page(req: Request):
    log = logging.getLogger("routers.terms")
    lang = getattr(req.state, "lang", settings.DEFAULT_LANG)
    site_id = _resolve_site_id(req)
    doc = legal_srv.get_latest_terms(site_id=site_id)
    if not doc:
        log.warning("terms of use missing for site_id=%s; rendering empty state", site_id)
        doc = {"sections": [], "content_html": ""}

    ctx = {
        "request": req,
        "lang": lang,
        "settings": settings,
        "terms": doc,
    }
    template_name = themed_name(req, "terms.html")
    return templates.TemplateResponse(template_name, ctx)
