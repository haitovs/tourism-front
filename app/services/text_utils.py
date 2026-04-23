# app/services/text_utils.py
from __future__ import annotations

import string

# Characters treated as "no content" when a paragraph/field contains only them.
# Covers ASCII punctuation + various dash glyphs admins paste in as placeholders.
_BLANK_CHARS = set(string.punctuation + string.whitespace + "—–‒―•·")


def _to_unix_newlines(s: str) -> str:
    s = (s or "")
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    while "\n\n\n" in s:
        s = s.replace("\n\n\n", "\n\n")
    return s


def is_blank_text(s: str | None) -> bool:
    if not s:
        return True
    return all(ch in _BLANK_CHARS for ch in s)


def normalize_paragraphs(s: str) -> list[str]:
    s = _to_unix_newlines(s).replace(" ", " ")
    parts = [p.strip() for p in s.split("\n\n")]
    return [p for p in parts if p and not is_blank_text(p)]


def split_short_and_topic(markdown_text: str) -> tuple[str, str]:
    paras = normalize_paragraphs(markdown_text or "")
    if not paras:
        return "", ""
    short = paras[0]
    topic = "\n\n".join(paras[1:]) if len(paras) > 1 else ""
    return short, topic


def normalize_textblock(s: str) -> str:
    paras = normalize_paragraphs(s or "")
    return "\n\n".join(paras)


def _strip_trailing_punct(s: str) -> str:
    return s.rstrip(".,;:!?·")


def compose_position_line(position: str | None, company: str | None) -> str:
    """Render 'position, company' but skip company when it's already spelled
    out inside position (case-insensitive). Handles the common admin mistake
    of typing the company name into the position field as well."""
    pos = (position or "").strip()
    comp = (company or "").strip()

    if not pos and not comp:
        return ""
    if not comp:
        return pos
    if not pos:
        return comp

    pos_norm = _strip_trailing_punct(pos).lower()
    comp_norm = _strip_trailing_punct(comp).lower()

    if comp_norm and comp_norm in pos_norm:
        return pos
    return f"{pos}, {comp}"
