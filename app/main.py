from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers.expo_sectors_router import router as expo_sectors_router
from app.routers.speaker_router import router as speaker_router

from .core.settings import settings
from .routers import htmx, site

app = FastAPI(title=settings.APP_NAME)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(site.router)
app.include_router(htmx.router)
app.include_router(speaker_router)
app.include_router(expo_sectors_router)
