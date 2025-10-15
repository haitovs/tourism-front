from __future__ import annotations

import re
from contextlib import contextmanager
from typing import Generator, Optional

import markdown as _md_lib
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.privacy_policy_model import PrivacyPolicy


@contextmanager
def _db_session() -> Generator[Session, None, None]:
    gen = get_db()
    db = next(gen)
    try:
        yield db
    finally:
        try:
            gen.close()
        except Exception:
            pass


def _md_to_html(md_text: str | None) -> str:
    if not md_text:
        return ""
    try:
        return _md_lib.markdown(
            md_text,
            extensions=["extra", "sane_lists", "toc", "attr_list", "nl2br"],
            output_format="html5",
        )
    except Exception:
        blocks = [b.strip() for b in (md_text or "").split("\n\n") if b.strip()]
        html_blocks = []
        for b in blocks:
            html_blocks.append("<p>" + b.replace("\n", "<br>") + "</p>")
        return "".join(html_blocks)


# Split sections by "## Heading" or "1. Heading"
_HEADING_RX = re.compile(r"^(?:\s{0,3}(?:#{2,6}\s+|(?:\d+)\.\s+))(?P<title>.+?)\s*$", re.MULTILINE)


def _split_sections(md_text: str) -> list[dict]:
    if not md_text:
        return []

    matches = list(_HEADING_RX.finditer(md_text))
    if not matches:
        return [{"title": "Introduction", "body_md": md_text.strip(), "body_html": _md_to_html(md_text)}]

    sections: list[dict] = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(md_text)
        title = m.group("title").strip()
        body_md = md_text[start:end].strip()
        sections.append({"title": title, "body_md": body_md, "body_html": _md_to_html(body_md)})
    return sections


def get_latest_privacy(*, site_id: Optional[int] = None) -> Optional[dict]:
    """
    Return the most recently updated published PrivacyPolicy for the site, or global fallback.
    """
    with _db_session() as db:
        base = select(PrivacyPolicy).where(PrivacyPolicy.published.is_(True))

        r = None
        if site_id is not None:
            r = (db.execute(base.where(PrivacyPolicy.site_id == site_id).order_by(desc(PrivacyPolicy.updated_at), desc(PrivacyPolicy.id)).limit(1)).scalars().first())

        if not r:
            r = (db.execute(base.order_by(desc(PrivacyPolicy.updated_at), desc(PrivacyPolicy.id)).limit(1)).scalars().first())

        if not r:
            return None

        return {
            "id": r.id,
            "title": r.title or "Privacy Policy",
            "version": r.version,
            "content_html": _md_to_html(r.content_md),
            "sections": _split_sections(r.content_md or ""),
            "created_at": r.created_at,
            "updated_at": r.updated_at,
        }
