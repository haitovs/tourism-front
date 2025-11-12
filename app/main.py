# app/main.py
import time
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.language_middleware import LanguageMiddleware
from app.core.settings import settings
from app.core.site_resolver import SiteResolverMiddleware
from app.routers.about_expo_router import router as about_expo_router
from app.routers.about_forum_router import router as about_forum_router
from app.routers.agenda_router import router as agenda_router
from app.routers.expo_sectors_router import router as expo_sectors_router
from app.routers.faq_router import router as faq_router
from app.routers.news_router import router as news_router
from app.routers.official_support_router import \
    router as official_support_router
from app.routers.participant_router import router as participant_router
from app.routers.privacy_router import router as privacy_router
from app.routers.site import router as site_router
from app.routers.speaker_router import router as speaker_router
from app.routers.terms_router import router as terms_router
from app.routers.timer_router import router as timer_router


@asynccontextmanager
async def lifespan(app):
    app.state.http = httpx.AsyncClient(
        timeout=httpx.Timeout(10.0, connect=2.0),
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        http2=True,
        follow_redirects=True,
    )
    try:
        yield
    finally:
        await app.state.http.aclose()


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)


@app.on_event("startup")
async def _set_assets_version():
    try:
        tw = Path(__file__).parent / "static" / "css" / "tw.build.css"
        mtime = int(tw.stat().st_mtime) if tw.exists() else int(time.time())
        settings.ASSETS_V = str(mtime)
        app.state.assets_v = settings.ASSETS_V
    except Exception:
        settings.ASSETS_V = str(int(time.time()))
        app.state.assets_v = settings.ASSETS_V


app.add_middleware(SiteResolverMiddleware)
app.add_middleware(LanguageMiddleware)


@app.get("/healthz")
def healthz():
    return {"ok": True}


app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(site_router)
app.include_router(speaker_router)
app.include_router(expo_sectors_router)
app.include_router(participant_router)
app.include_router(news_router)
app.include_router(about_forum_router)
app.include_router(about_expo_router)
app.include_router(faq_router)
app.include_router(official_support_router)
app.include_router(terms_router)
app.include_router(privacy_router)
app.include_router(agenda_router)
app.include_router(timer_router)
