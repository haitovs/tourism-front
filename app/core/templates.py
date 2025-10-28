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
_THEME_TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "_themes"


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


@pass_context
def site_slug(ctx) -> str:
    req = ctx.get("request")
    s = getattr(getattr(req, "state", None), "site", None)
    return getattr(s, "slug", None) or getattr(settings, "FRONT_SITE_SLUG", "") or ""


@pass_context
def theme(ctx, path: str) -> str:
    slug = site_slug(ctx)
    sub = settings.THEME_STATIC_SUBDIR.strip("/")
    p = path.lstrip("/")
    if slug:
        return f"/static/{sub}/{slug}/{p}"
    return f"/static/{p}"


@pass_context
def themed(ctx, path: str) -> str:
    """Return themed template path if exists, else the given path."""
    slug = site_slug(ctx)
    p = path.lstrip("/")
    if slug:
        candidate = _THEME_TEMPLATES_DIR / slug / p
        if candidate.exists():
            return f"_themes/{slug}/{p}"
    return p


@pass_context
def is_site(ctx, slug: str) -> bool:
    return (slug or "") == site_slug(ctx)


templates = Jinja2Templates(directory="app/templates", auto_reload=settings.ENV == "dev")
templates.env.globals["t"] = t
templates.env.globals["lang_ctx"] = lang_ctx
templates.env.globals["theme"] = theme
templates.env.globals["themed"] = themed
templates.env.globals["site_slug"] = site_slug
templates.env.globals["is_site"] = is_site
