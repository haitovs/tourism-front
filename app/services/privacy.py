from __future__ import annotations

import html
from typing import Optional
import re

from fastapi import Request

from app.core.http import api_get


def _simple_html(text: str | None) -> str:
    raw = (text or "").strip()
    if not raw:
        return ""
    safe = html.escape(raw)
    blocks = [blk.strip() for blk in safe.split("\n\n") if blk.strip()]
    if not blocks:
        return "<p>" + safe.replace("\n", "<br>") + "</p>" if safe else ""
    rendered = []
    for blk in blocks:
        rendered.append("<p>" + blk.replace("\n", "<br>") + "</p>")
    return "".join(rendered)

# Split markdown by headings (## or "1. Title")
_HEADING_RX = re.compile(r"^\s*(?:#{2,6}\s+|\d+\.\s+)(?P<title>.+?)\s*$", re.MULTILINE)


def _split_sections(md_text: str) -> list[dict]:
    if not md_text:
        return []

    matches = list(_HEADING_RX.finditer(md_text))
    if not matches:
        return [{"title": "Introduction", "body_md": md_text.strip(), "body_html": _simple_html(md_text)}]

    sections: list[dict] = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(md_text)
        title = m.group("title").strip()
        body_md = md_text[start:end].strip()
        sections.append({"title": title, "body_md": body_md, "body_html": _simple_html(body_md)})
    return sections


async def get_latest_privacy(req: Request, *, site_id: Optional[int] = None) -> Optional[dict]:
    import logging

    log = logging.getLogger("services.privacy")
    try:
        data = await api_get(req, "/privacy-policy/latest", soft=True)
        if not data:
            return None

        content_md = data.get("content_md") or ""
        content_html = _simple_html(content_md)
        sections = _split_sections(content_md)

        return {
            "id": data.get("id"),
            "title": data.get("title") or "Privacy Policy",
            "version": data.get("version"),
            "sections": sections,
            "content_html": content_html if not sections else "",
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
            "first_section_title": sections[0]["title"] if sections else data.get("title"),
        }
    except Exception as exc:
        log.exception("get_latest_privacy unexpected: %r", exc)
        return None
