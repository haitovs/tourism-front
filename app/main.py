from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .routers import site, htmx
from .core.settings import settings

app = FastAPI(title=settings.APP_NAME)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(site.router)
app.include_router(htmx.router)
