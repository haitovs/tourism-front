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
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


@pass_context
def t(ctx, key: str) -> str:
    """
    Usage in templates: {{ t("nav.home") }}
    Falls back to English and then to the key itself.
    """
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
    """
    Returns current language from request.state.lang.
    Usage (if needed): {{ lang_ctx() }}
    """
    request = ctx.get("request")
    return getattr(getattr(request, "state", None), "lang", settings.DEFAULT_LANG)


# Standard templates env
templates = Jinja2Templates(directory="app/templates", auto_reload=True)

# Register helpers as Jinja globals
templates.env.globals["t"] = t
templates.env.globals["lang_ctx"] = lang_ctx
