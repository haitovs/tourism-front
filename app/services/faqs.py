# app/services/faq.py
from __future__ import annotations

from fastapi import Request

from app.core.http import api_get


async def list_faqs(
    req: Request,
    *,
    limit: int | None = None,
) -> list[dict]:
    """
    Return published FAQs from backend (already localized via ?lang cookie/header),
    preserving the {id, question, answer_md} shape used by templates.
    """
    params = {}
    if limit:
        params["limit"] = max(1, int(limit))

    items = await api_get(req, "/faq/", params=params or None)

    return [{
        "id": it.get("id"),
        "question": it.get("question") or "",
        "answer_md": it.get("answer_md") or "",
    } for it in (items or [])]
