# app/routers/news_router.py
from __future__ import annotations

import math

from fastapi import APIRouter, HTTPException, Query, Request
from starlette import status
from starlette.responses import HTMLResponse

from app.services import news as news_srv

from ..core.settings import settings
from ..core.templates import templates, themed_name

router = APIRouter()


def _filter_news(items: list[dict], q: str | None) -> list[dict]:
    if not q:
        return items
    ql = q.strip().lower()
    if not ql:
        return items
    return [n for n in items if ql in str(n.get("title", "")).lower() or ql in str(n.get("summary", "")).lower()]


@router.get("/news", response_class=HTMLResponse)
async def news_list(
        req: Request,
        q: str | None = Query(None),
        page: int = Query(1, ge=1),
        per_page: int = Query(6, ge=1, le=24),
):
    lang = getattr(req.state, "lang", settings.DEFAULT_LANG)
    all_items = await news_srv.get_latest_news(req, limit=200)
    all_items = _filter_news(all_items, q)

    if page == 1:
        visual_take = min(5, len(all_items))
        items = all_items[:visual_take]
        total_remaining = max(0, len(all_items) - visual_take)
        grid_per_page = per_page
        total_pages = 1 + (math.ceil(total_remaining / grid_per_page) if total_remaining else 0)
    else:
        start_idx = 5 + (page - 2) * per_page
        end_idx = start_idx + per_page
        items = all_items[start_idx:end_idx]
        total_remaining = max(0, len(all_items) - 5)
        total_pages = 1 + (math.ceil(total_remaining / per_page) if total_remaining else 0)

    ctx = {
        "request": req,
        "lang": lang,
        "q": q or "",
        "items": items,
        "page": page,
        "per_page": per_page,
        "total_pages": max(total_pages, 1),
    }
    template_name = themed_name(req, "news.html")
    return templates.TemplateResponse(template_name, ctx)


@router.get("/news/{news_id}", response_class=HTMLResponse)
async def news_detail(req: Request, news_id: int):
    lang = getattr(req.state, "lang", settings.DEFAULT_LANG)
    record = await news_srv.get_news(req, news_id=news_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News not found")
    ctx = {"request": req, "lang": lang, "settings": settings, "item": record}
    template_name = themed_name(req, "news_detail.html")
    return templates.TemplateResponse(template_name, ctx)
