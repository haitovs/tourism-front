# app/routers/internal_cache_router.py
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query
from starlette import status

from app.core.settings import settings
from app.services import speakers as speakers_srv

router = APIRouter(prefix="/internal/cache", tags=["internal"])


_INVALIDATORS = {
    "speakers": speakers_srv.invalidate_caches,
    "all": speakers_srv.invalidate_caches,
}


def _check_token(authorization: str | None, token_q: str | None) -> None:
    expected = (settings.INTERNAL_CACHE_TOKEN or "").strip()
    if not expected:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="invalidation disabled")

    provided = ""
    if authorization:
        parts = authorization.split(None, 1)
        provided = parts[1].strip() if len(parts) == 2 and parts[0].lower() == "bearer" else authorization.strip()
    if not provided and token_q:
        provided = token_q.strip()

    if provided != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")


@router.post("/invalidate")
async def invalidate(
    kind: str = Query("speakers"),
    authorization: str | None = Header(default=None),
    token: str | None = Query(default=None),
):
    _check_token(authorization, token)
    fn = _INVALIDATORS.get(kind)
    if not fn:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"unknown kind: {kind}")
    fn()
    return {"ok": True, "kind": kind}
