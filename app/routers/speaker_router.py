# app/routers/site.py
from fastapi import APIRouter, HTTPException, Request
from starlette import status
from starlette.responses import HTMLResponse

from app.services import speakers as speakers_srv

from ..core.settings import settings
from ..core.templates import templates

router = APIRouter()


# ---------- Speakers: list page ----------
@router.get("/speakers", response_class=HTMLResponse)
async def speakers_page(req: Request, page: int = 1):
    lang = getattr(req.state, "lang", settings.DEFAULT_LANG)

    q = req.query_params.get("q") or ""

    items, total_pages, total_items = speakers_srv.list_speakers_page(page=page, per_page=9)

    ctx = {
        "request": req,
        "lang": lang,
        "settings": settings,
        "speakers": items,
        "current_page": page,
        "total_pages": total_pages,
        "total_items": total_items,
        "q": q,
    }
    return templates.TemplateResponse("speakers.html", ctx)


# ---------- Speakers: detail page ----------
@router.get("/speakers/{speaker_id}", response_class=HTMLResponse)
async def speaker_detail(req: Request, speaker_id: int):
    lang = getattr(req.state, "lang", settings.DEFAULT_LANG)
    sp = speakers_srv.get_speaker(speaker_id=speaker_id)
    if not sp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Speaker not found")

    ctx = {
        "request": req,
        "lang": lang,
        "settings": settings,
        "speaker": sp,
    }
    return templates.TemplateResponse("speaker_detail.html", ctx)
