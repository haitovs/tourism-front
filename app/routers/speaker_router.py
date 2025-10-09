# app/routers/site.py
from fastapi import APIRouter, HTTPException, Request
from starlette import status
from starlette.responses import HTMLResponse

from app.routers.site import _resolve_lang
from app.services import speakers as speakers_srv

from ..core.settings import settings
from ..core.templates import templates

router = APIRouter()


# ---------- Speakers: list page ----------
@router.get("/speakers", response_class=HTMLResponse)
async def speakers_page(req: Request):
    lang = _resolve_lang(req)
    speakers = speakers_srv.list_speakers()  # all speakers (ordered latest first)

    ctx = {
        "request": req,
        "lang": lang,
        "settings": settings,
        "speakers": speakers,
    }
    return templates.TemplateResponse("speakers.html", ctx)


# ---------- Speakers: detail page ----------
@router.get("/speakers/{speaker_id}", response_class=HTMLResponse)
async def speaker_detail(req: Request, speaker_id: int):
    lang = _resolve_lang(req)
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
