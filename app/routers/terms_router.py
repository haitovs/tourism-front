# app/routers/terms_router.py
from fastapi import APIRouter, HTTPException, Request
from starlette import status
from starlette.responses import HTMLResponse

from app.routers.site import _resolve_lang, _resolve_site_id
from app.services import terms as legal_srv

from ..core.settings import settings
from ..core.templates import templates

router = APIRouter()


@router.get("/terms", response_class=HTMLResponse)
async def terms_of_use_page(req: Request):
    lang = _resolve_lang(req)
    site_id = _resolve_site_id(req)
    doc = legal_srv.get_latest_terms(site_id=site_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Terms of Use not found")

    ctx = {
        "request": req,
        "lang": lang,
        "settings": settings,
        "terms": doc,
    }
    return templates.TemplateResponse("terms.html", ctx)
