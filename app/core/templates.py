# app/core/templates.py
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict

from jinja2 import pass_context
from starlette.templating import Jinja2Templates

from app.core.settings import settings

_LOCALES_DIR = Path(__file__).parent.parent / "locales"


@lru_cache(maxsize=64)
def _load_locale(lang: str) -> Dict[str, str]:
    path = _LOCALES_DIR / f"{lang}.json"
    if not path.exists():
        print(f"[i18n] missing locale: {path}")
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        print(f"[i18n] loaded {lang}: {len(data)} keys")
        return data
    except Exception as e:
        print(f"[i18n] failed to load {path}: {e}")
        return {}


@pass_context
def t(ctx, key: str) -> str:
    request = ctx.get("request")
    lang = getattr(getattr(request, "state", None), "lang", settings.DEFAULT_LANG)
    d_lang = _load_locale(lang)
    if key in d_lang and d_lang[key]:
        return d_lang[key]
    d_en = _load_locale(settings.DEFAULT_LANG)
    if key in d_en and d_en[key]:
        return d_en[key]
    return key


@pass_context
def lang_ctx(ctx) -> str:
    request = ctx.get("request")
    return getattr(getattr(request, "state", None), "lang", settings.DEFAULT_LANG)


templates = Jinja2Templates(directory="app/templates", auto_reload=settings.ENV == "dev")

templates.env.globals["t"] = t
templates.env.globals["lang_ctx"] = lang_ctx
