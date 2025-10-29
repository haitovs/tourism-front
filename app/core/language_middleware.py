# app/core/language_middleware.py
from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.settings import settings

LANG_COOKIE = "lang"


def _normalize_lang(code: str | None) -> str:
    if not code:
        return settings.DEFAULT_LANG
    code = code.lower().strip()
    # allow zh-CN → zh etc.
    code2 = code.split("-")[0]
    return code2 if code2 in settings.SUPPORTED_LANGS else settings.DEFAULT_LANG


class LanguageMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        q = request.query_params.get("lang")
        c = request.cookies.get(LANG_COOKIE)
        al = (request.headers.get("accept-language") or "").split(",")[0] or ""
        lang = _normalize_lang(q or c or al)

        request.state.lang = lang
        response = await call_next(request)

        # refresh cookie if missing/changed
        if c != lang:
            response.set_cookie(LANG_COOKIE, lang, max_age=60 * 60 * 24 * 365, samesite="lax")
        return response
