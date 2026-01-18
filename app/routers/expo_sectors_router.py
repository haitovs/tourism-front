# app/routers/expo_sectors_router.py
from fastapi import APIRouter, HTTPException, Request
from starlette import status
from starlette.responses import HTMLResponse

from app.services import expo_sectors as sectors_srv

from ..core.settings import settings
from ..core.templates import templates, themed_name

router = APIRouter()


@router.get("/expo-sectors", response_class=HTMLResponse)
async def expo_sectors_page(req: Request):
    lang = getattr(req.state, "lang", settings.DEFAULT_LANG)
    # ⬇️ pass req and await the async function
    sectors = await sectors_srv.list_home_sectors(req, limit=1000, latest_first=False)
    ctx = {"request": req, "lang": lang, "settings": settings, "sectors": sectors}
    template_name = themed_name(req, "expo_sectors.html")
    return templates.TemplateResponse(template_name, ctx)


@router.get("/expo-sectors/{sector_id}", response_class=HTMLResponse)
async def expo_sector_detail(req: Request, sector_id: int):
    lang = getattr(req.state, "lang", settings.DEFAULT_LANG)
    # ⬇️ pass req and await the async function
    sector = await sectors_srv.get_sector(req=req, sector_id=sector_id)
    if not sector:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sector not found")

    debug = req.query_params.get("debug")
    ctx = {"request": req, "lang": lang, "settings": settings, "sector": sector, "debug": debug}
    template_name = themed_name(req, "expo_sector_detail.html")
    return templates.TemplateResponse(template_name, ctx)
