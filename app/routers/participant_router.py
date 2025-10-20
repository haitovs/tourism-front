# app/routers/participants_router.py
from fastapi import APIRouter, HTTPException, Request
from starlette import status
from starlette.responses import HTMLResponse

from app.services import participants as participants_srv

from ..core.settings import settings
from ..core.templates import templates

router = APIRouter()


@router.get("/participants", response_class=HTMLResponse)
async def participants_page(req: Request):
    """
    Grid/list page.
    Optional query params:
      - role: expo|forum|both
      - q: search by name (contains)
    """
    lang = getattr(req.state, "lang", settings.DEFAULT_LANG)
    role = req.query_params.get("role")
    q = req.query_params.get("q")
    # You can pass site_id here if you already derive it per-tenant elsewhere.
    items = participants_srv.list_participants(limit=1000, latest_first=False, role=role, q=q)
    ctx = {
        "request": req,
        "lang": lang,
        "settings": settings,
        "participants": items,
        "role": role,
        "q": q,
    }
    return templates.TemplateResponse("participants.html", ctx)


@router.get("/participants/{participant_id}", response_class=HTMLResponse)
async def participant_detail(req: Request, participant_id: int):
    lang = getattr(req.state, "lang", settings.DEFAULT_LANG)
    participant = participants_srv.get_participant(participant_id=participant_id)
    if not participant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found")

    debug = req.query_params.get("debug")
    ctx = {
        "request": req,
        "lang": lang,
        "settings": settings,
        "participant": participant,
        "debug": debug,
    }
    return templates.TemplateResponse("participant_detail.html", ctx)
