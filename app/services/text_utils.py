# app/services/text_utils.py
from __future__ import annotations


def _to_unix_newlines(s: str) -> str:
    s = (s or "")
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    while "\n\n\n" in s:
        s = s.replace("\n\n\n", "\n\n")
    return s


def normalize_paragraphs(s: str) -> list[str]:
    s = _to_unix_newlines(s).replace("\u00A0", " ")
    parts = [p.strip() for p in s.split("\n\n")]
    return [p for p in parts if p]


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
