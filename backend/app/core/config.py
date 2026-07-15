from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Supabase / Postgres
    database_url: str
    supabase_url: str
    supabase_jwt_secret: str

    # Meta Ads (usado desde el Módulo 2 en adelante)
    meta_app_id: str = ""
    meta_app_secret: str = ""

    environment: str = "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
