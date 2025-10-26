# app/services/news.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import Request

from app.core.http import api_get
from app.core.settings import settings


def _resolve_media(path: str | None) -> str:
    if not path:
        return ""
    low = path.lower()
    if low.startswith("http://") or low.startswith("https://"):
        return path
    base = settings.MEDIA_BASE_URL.rstrip("/")
    pref = settings.MEDIA_PREFIX.strip("/")
    if path.startswith("/"):
        return f"{base}/{path.lstrip('/')}"
    return f"{base}/{pref}/{path.lstrip('/')}" if pref else f"{base}/{path.lstrip('/')}"


def _date_parts(iso_str: Optional[str]) -> tuple[Optional[str], str]:
    if not iso_str:
        return None, ""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.isoformat(), dt.strftime("%d %b %y")
    except Exception:
        return iso_str, ""


def _row_to_card(row: dict) -> dict:
    date_iso, date_human = _date_parts(row.get("created_at"))
    return {
        "id": row.get("id"),
        "title": row.get("header") or "",
        "summary": row.get("description") or "",
        "category": row.get("category") or "News",
        "image_url": _resolve_media(row.get("photo")),
        "date_iso": date_iso,
        "date_human": date_human,
    }


async def get_latest_news(
    req: Request,
    *,
    limit: int = 5,
    include_unpublished: bool = False,
) -> list[dict]:
    import asyncio
    import logging

    import httpx
    log = logging.getLogger("services.news")

    items = None
    for attempt in range(2):
        try:
            items = await api_get(req, f"/news/?skip=0&limit={max(1, int(limit))}")
            break
        except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
            log.warning("get_latest_news timeout (attempt %d/2): %s", attempt + 1, e)
            if attempt == 0:
                await asyncio.sleep(0.35)
                continue
        except httpx.HTTPError as e:
            log.error("get_latest_news HTTP error: %r", e)
            break
        except Exception as e:
            log.exception("get_latest_news unexpected: %r", e)
            break

    items = items or []

    if not include_unpublished:
        items = [it for it in items if it.get("is_published", True)]

    def _sort_key(it: dict):
        return (it.get("created_at") or "", it.get("id") or 0)

    items.sort(key=_sort_key, reverse=True)
    items = items[:max(1, int(limit))]

    return [_row_to_card(it) for it in items]


async def get_news(
    req: Request,
    news_id: int,
) -> Optional[dict]:
    import asyncio
    import logging

    import httpx
    log = logging.getLogger("services.news")

    row = None
    for attempt in range(2):
        try:
            row = await api_get(req, f"/news/{news_id}")
            break
        except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
            log.warning("get_news[%s] timeout (attempt %d/2): %s", news_id, attempt + 1, e)
            if attempt == 0:
                await asyncio.sleep(0.35)
                continue
        except httpx.HTTPError as e:
            log.error("get_news[%s] HTTP error: %r", news_id, e)
            return None
        except Exception as e:
            log.exception("get_news[%s] unexpected: %r", news_id, e)
            return None

    if not row:
        return None

    card = _row_to_card(row)
    card["body"] = row.get("body") or row.get("description") or ""
    return card
