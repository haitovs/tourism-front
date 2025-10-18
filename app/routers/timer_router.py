# app/routers/timer.py
from fastapi import APIRouter, Request
from starlette.responses import JSONResponse

from app.services.timer import build_timer_context, get_deadline_from_settings

from ..core.settings import settings

router = APIRouter()


@router.get("/api/timer", response_class=JSONResponse)
async def timer_info(req: Request):
    """
    Returns JSON:
    {
      "deadline_iso_utc": "...Z",
      "deadline_month_upper": "AUGUST",
      "deadline_day": 25
    }
    """
    deadline_dt = get_deadline_from_settings(settings)
    ctx = build_timer_context(deadline_dt)
    return JSONResponse(ctx)
