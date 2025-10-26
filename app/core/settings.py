# app/core/settings.py
from typing import Tuple

from pydantic import Field  # <-- add this
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",  # <-- ignore env keys you don't map to fields
        populate_by_name=True,  # <-- allow alias population
    )

    ENV: str = "dev"
    APP_NAME: str = "Expo Site"
    DATABASE_URL: str = "postgresql+psycopg2://forum_admin:admin@localhost:5432/forum_app"

    TRANSLATE_BASE_URL: str = "https://libretranslate.de"
    TRANSLATE_API_KEY: str | None = None

    # --- I18N (front) ---
    DEFAULT_LANG: str = "en"
    SUPPORTED_LANGS_RAW: str = Field(default="en,ru,tk,zh", alias="SUPPORTED_LANGS")

    MEDIA_BASE_URL: str = "http://localhost:8000"
    MEDIA_PREFIX: str = "/uploads"

    BACKEND_BASE_URL: str = "http://127.0.0.1:8000"
    BACKEND_HOST_HEADER: str | None = None
    STATS_BG_IMAGE: str = "/static/img/stats_bg.png"

    FRONT_SITE_ID: int = 10

    @property
    def SUPPORTED_LANGS(self) -> Tuple[str, ...]:
        items = [x.strip().lower() for x in self.SUPPORTED_LANGS_RAW.split(",") if x.strip()]
        seen, out = set(), []
        for x in items:
            k = x.split("-")[0]
            if k and k not in seen:
                seen.add(k)
                out.append(k)
        if self.DEFAULT_LANG not in out:
            out.insert(0, self.DEFAULT_LANG)
        return tuple(out)


settings = Settings()
