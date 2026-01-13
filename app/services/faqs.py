# app/services/faq.py
from __future__ import annotations

from fastapi import Request

from app.core.http import api_get


async def list_faqs(
    req: Request,
    *,
    limit: int | None = None,
) -> list[dict]:
    import asyncio
    import logging

    import httpx
    log = logging.getLogger("services.faq")

    params = {}
    if limit:
        params["limit"] = max(1, int(limit))

    items = None
    for attempt in range(2):
        try:
            items = await api_get(req, "/faq", params=params or None)
            break
        except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
            log.warning("list_faqs timeout (attempt %d/2): %s", attempt + 1, e)
            if attempt == 0:
                await asyncio.sleep(0.3)
                continue
        except httpx.HTTPError as e:
            log.error("list_faqs HTTP error: %r", e)
            break
        except Exception as e:
            log.exception("list_faqs unexpected: %r", e)
            break

    return [{
        "id": it.get("id"),
        "question": it.get("question") or "",
        "answer_md": it.get("answer_md") or "",
    } for it in (items or [])]
