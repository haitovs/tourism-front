# app/core/templates.py
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict

from jinja2 import pass_context
from starlette.requests import Request
from starlette.templating import Jinja2Templates

from app.core.settings import settings

_BASE_DIR = Path(__file__).parent.parent
_LOCALES_DIR = _BASE_DIR / "locales"
_TEMPLATES_DIR = _BASE_DIR / "templates"
_STATIC_DIR = _BASE_DIR / "static"
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


@lru_cache(maxsize=512)
def _resolve_themed_path(slug: str | None, path: str) -> str | None:
    p = path.lstrip("/")
    if not slug:
        return None
    candidate = _THEME_TEMPLATES_DIR / slug / p
    if candidate.exists():
        return f"_themes/{slug}/{p}"
    return None


def themed_name(req: Request | None, path: str) -> str:
    slug = None
    if req is not None:
        site = getattr(req.state, "site", None)
        slug = getattr(site, "slug", None)
    resolved = _resolve_themed_path(slug, path)
    return resolved or path.lstrip("/")


@lru_cache(maxsize=256)
def _resolve_theme_asset(slug: str | None, rel_path: str) -> str | None:
    if not slug:
        return None
    sub = settings.THEME_STATIC_SUBDIR.strip("/")
    rel = rel_path.lstrip("/")
    candidate = _STATIC_DIR / sub / slug / rel
    if candidate.exists():
        return f"/static/{sub}/{slug}/{rel}"
    return None


@pass_context
def site_slug(ctx) -> str:
    req = ctx.get("request")
    s = getattr(getattr(req, "state", None), "site", None)
    return getattr(s, "slug", "") or ""


@pass_context
def theme(ctx, path: str) -> str:
    slug = site_slug(ctx)
    rel = path.lstrip("/")
    themed_asset = _resolve_theme_asset(slug, rel)
    if themed_asset:
        return themed_asset
    return f"/static/{rel}"


@pass_context
def themed(ctx, path: str) -> str:
    req = ctx.get("request")
    return themed_name(req, path)


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
templates.env.globals["settings"] = settings
