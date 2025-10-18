from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers.about_expo_router import router as about_forum_router
from app.routers.about_forum_router import router as about_expo_router
from app.routers.agenda_router import router as agenda_router
from app.routers.expo_sectors_router import router as expo_sectors_router
from app.routers.faq_router import router as faq_router
from app.routers.news_router import router as news_router
from app.routers.official_support_router import \
    router as official_support_router
from app.routers.participant_router import router as participant_router
from app.routers.privacy_router import router as privacy_router
from app.routers.speaker_router import router as speaker_router
from app.routers.terms_router import router as terms_router
from app.routers.timer_router import router as timer_router

from .core.settings import settings
from .routers import site

app = FastAPI(title=settings.APP_NAME)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(site.router)
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
