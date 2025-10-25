# app/routers/participants_router.py
from fastapi import APIRouter, HTTPException, Query, Request
from starlette import status
from starlette.responses import HTMLResponse, JSONResponse

from app.services import participants as participants_srv

from ..core.settings import settings
from ..core.templates import templates

router = APIRouter()


@router.get("/participants", response_class=HTMLResponse)
async def participants_page(req: Request):
    lang = getattr(req.state, "lang", settings.DEFAULT_LANG)
    role = req.query_params.get("role")
    q = req.query_params.get("q")

    items = await participants_srv.list_participants(req, limit=12, offset=0, latest_first=False, role=role, q=q)
    ctx = {"request": req, "lang": lang, "settings": settings, "participants": items, "role": role, "q": q}
    return templates.TemplateResponse("participants.html", ctx)


@router.get("/api/participants", response_class=JSONResponse)
async def participants_api(
        req: Request,
        role: str | None = Query(default=None),
        q: str | None = Query(default=None),
        limit: int = Query(default=12, ge=1, le=60),
        offset: int = Query(default=0, ge=0),
):
    items = await participants_srv.list_participants(req, limit=limit + 1, offset=offset, latest_first=False, role=role, q=q)
    has_more = len(items) > limit
    items = items[:limit]
    next_offset = offset + limit if has_more else None
    return JSONResponse({"items": items, "next_offset": next_offset})


@router.get("/participants/{participant_id}", response_class=HTMLResponse)
async def participant_detail(req: Request, participant_id: int):
    lang = getattr(req.state, "lang", settings.DEFAULT_LANG)
    participant = await participants_srv.get_participant(req, participant_id=participant_id)
    if not participant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found")
    debug = req.query_params.get("debug")
    ctx = {"request": req, "lang": lang, "settings": settings, "participant": participant, "debug": debug}
    return templates.TemplateResponse("participant_detail.html", ctx)
