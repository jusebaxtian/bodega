from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Supabase / Postgres
    database_url: str
    supabase_url: str
    supabase_jwt_secret: str

    # Meta Ads (solo lectura: ads_read + business_management, nunca ads_management)
    meta_app_id: str = ""
    meta_app_secret: str = ""
    meta_redirect_uri: str = "http://localhost:3000/integrations/meta/callback"
    meta_api_version: str = "v21.0"

    # Clave Fernet para cifrar el access_token de Meta en reposo
    token_encryption_key: str = "BuuvlSwu6W7Z5egpexvmou5-8_ZMmRYP4l8x0aYb9P8="

    # IA (Módulo 4) — la IA solo redacta el diagnóstico, no calcula métricas
    anthropic_api_key: str = ""

    environment: str = "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
