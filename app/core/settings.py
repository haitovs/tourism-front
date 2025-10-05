from typing import Tuple

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    ENV: str = "dev"
    APP_NAME: str = "Expo Site"
    DATABASE_URL: str = "postgresql+psycopg2://forum_admin:admin@localhost:5432/forum_app"

    TRANSLATE_BASE_URL: str = "https://libretranslate.de"
    TRANSLATE_API_KEY: str | None = None

    DEFAULT_LANG: str = "en"
    SUPPORTED_LANGS: Tuple[str, ...] = ("en", "ru", "tm")

    MEDIA_BASE_URL: str = "http://localhost:8000"
    MEDIA_PREFIX: str = "/uploads"

    BACKEND_BASE_URL: str = "http://127.0.0.1:8000"
    STATS_BG_IMAGE: str = "/static/img/stats_bg.png"


settings = Settings()
