# app/routers/privacy_router.py
from fastapi import APIRouter, HTTPException, Request
from starlette import status
from starlette.responses import HTMLResponse

from app.routers.site import _resolve_site_id
from app.services import privacy as legal_srv

from ..core.settings import settings
from ..core.templates import templates

router = APIRouter()


@router.get("/privacy", response_class=HTMLResponse)
async def privacy_policy_page(req: Request):
    lang = getattr(req.state, "lang", settings.DEFAULT_LANG)
    site_id = _resolve_site_id(req)
    doc = legal_srv.get_latest_privacy(site_id=site_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Privacy Policy not found")

    ctx = {
        "request": req,
        "lang": lang,
        "settings": settings,
        "privacy": doc,
    }
    return templates.TemplateResponse("privacy.html", ctx)
