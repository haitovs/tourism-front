from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse

from app.core.templates import templates, themed_name

router = APIRouter()


@router.get("/official-support", response_class=HTMLResponse)
async def official_support_page(request: Request):
    template_name = themed_name(request, "official_support.html")
    return templates.TemplateResponse(template_name, {"request": request})
