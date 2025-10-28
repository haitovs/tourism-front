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
_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
_THEME_TEMPLATES_DIR = _TEMPLATES_DIR / "_themes"


@lru_cache(maxsize=128)
def _load_locale(lang: str) -> Dict[str, str]:
    p = _LOCALES_DIR / f"{lang}.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


@lru_cache(maxsize=128)
def _load_theme_locale(slug: str | None, lang: str) -> Dict[str, str]:
    if not slug:
        return {}
    p = _THEME_TEMPLATES_DIR / slug / "locales" / f"{lang}.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


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


@pass_context
def t(ctx, key: str) -> str:
    req = ctx.get("request")
    lang = getattr(getattr(req, "state", None), "lang", settings.DEFAULT_LANG)
    slug = site_slug(ctx)

    # 1) Theme override (lang → default EN)
    if slug:
        td = _load_theme_locale(slug, lang)
        if key in td and td[key]:
            return td[key]
        t_en = _load_theme_locale(slug, settings.DEFAULT_LANG)
        if key in t_en and t_en[key]:
            return t_en[key]

    # 2) Global (lang → default EN)
    d_lang = _load_locale(lang)
    if key in d_lang and d_lang[key]:
        return d_lang[key]
    d_en = _load_locale(settings.DEFAULT_LANG)
    if key in d_en and d_en[key]:
        return d_en[key]

    return key


@pass_context
def lang_ctx(ctx) -> str:
    req = ctx.get("request")
    return getattr(getattr(req, "state", None), "lang", settings.DEFAULT_LANG)


templates = Jinja2Templates(directory="app/templates", auto_reload=settings.ENV == "dev")
templates.env.globals["t"] = t
templates.env.globals["lang_ctx"] = lang_ctx
templates.env.globals["theme"] = theme
templates.env.globals["themed"] = themed
templates.env.globals["site_slug"] = site_slug
templates.env.globals["is_site"] = is_site
