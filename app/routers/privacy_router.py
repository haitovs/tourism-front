# app/routers/privacy_router.py
import logging

from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse

from app.routers.site import _resolve_site_id
from app.services import privacy as legal_srv

from ..core.settings import settings
from ..core.templates import templates, themed_name

router = APIRouter()


@router.get("/privacy", response_class=HTMLResponse)
async def privacy_policy_page(req: Request):
    log = logging.getLogger("routers.privacy")
    lang = getattr(req.state, "lang", settings.DEFAULT_LANG)
    site_id = _resolve_site_id(req)
    doc = await legal_srv.get_latest_privacy(req, site_id=site_id)
    if not doc:
        log.warning("privacy policy missing for site_id=%s; rendering empty state", site_id)
        doc = {"sections": [], "content_html": ""}

    ctx = {
        "request": req,
        "lang": lang,
        "settings": settings,
        "privacy": doc,
    }
    template_name = themed_name(req, "privacy.html")
    return templates.TemplateResponse(template_name, ctx)
