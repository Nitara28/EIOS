import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


# EIOS project root:
# backend/app/core/config.py
# -> backend
# -> EIOS
BASE_DIR = Path(__file__).resolve().parents[3]
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    PROJECT_NAME: str = "EIOS — AI COO"
    API_V1_STR: str = "/api/v1"

    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "eios_super_secret_jwt_key_change_in_production_32bytes"
    )

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./eios.db"
    )

    # Gemini AI
    GEMINI_API_KEY: Optional[str] = None

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"

    # Gmail OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = (
        "http://localhost:8000/api/v1/connectors/gmail/callback"
    )

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()