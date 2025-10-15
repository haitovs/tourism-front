from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse

from app.core.templates import templates

router = APIRouter()


@router.get("/official-support", response_class=HTMLResponse)
async def official_support_page(request: Request):
    return templates.TemplateResponse("official_support.html", {"request": request})
