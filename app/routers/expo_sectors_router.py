# app/routers/expo_sectors_router.py
from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse

from app.routers.site import _resolve_lang
from app.services import expo_sectors as sectors_srv

from ..core.settings import settings
from ..core.templates import templates

router = APIRouter()


@router.get("/expo-sectors", response_class=HTMLResponse)
async def expo_sectors_page(req: Request):
    lang = _resolve_lang(req)

    # Use existing service; large limit to effectively show all.
    sectors = sectors_srv.list_home_sectors(limit=1000, latest_first=False)

    ctx = {
        "request": req,
        "lang": lang,
        "settings": settings,
        "sectors": sectors,
    }
    return templates.TemplateResponse("expo_sectors.html", ctx)
