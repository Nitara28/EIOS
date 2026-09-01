import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List, Union

# EIOS project root:
# backend/app/core/config.py -> backend -> EIOS
BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE_BACKEND = BASE_DIR / ".env"
ENV_FILE_ROOT = BASE_DIR.parent / ".env"

class Settings(BaseSettings):
    PROJECT_NAME: str = "EIOS — AI COO"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "eios_super_secret_jwt_key_change_in_production_32bytes"
    )

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    ALGORITHM: str = "HS256"

    # Database Configuration (Supports SQLite for local dev & PostgreSQL for prod)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./eios.db"
    )

    # CORS & Frontend URLs
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    CORS_ORIGINS: Union[str, List[str]] = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")

    # Gemini AI API Key
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)

    # Redis / Celery
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Google Gmail OAuth Connector
    GOOGLE_CLIENT_ID: Optional[str] = os.getenv("GOOGLE_CLIENT_ID", None)
    GOOGLE_CLIENT_SECRET: Optional[str] = os.getenv("GOOGLE_CLIENT_SECRET", None)
    GOOGLE_REDIRECT_URI: str = os.getenv(
        "GOOGLE_REDIRECT_URI",
        "http://localhost:8000/api/v1/connectors/gmail/callback"
    )

    # WhatsApp Business Cloud API Connector
    WHATSAPP_ACCESS_TOKEN: Optional[str] = os.getenv("WHATSAPP_ACCESS_TOKEN", None)
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = os.getenv("WHATSAPP_PHONE_NUMBER_ID", None)
    WHATSAPP_BUSINESS_ACCOUNT_ID: Optional[str] = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", None)
    WHATSAPP_APP_ID: Optional[str] = os.getenv("WHATSAPP_APP_ID", None)
    WHATSAPP_APP_SECRET: Optional[str] = os.getenv("WHATSAPP_APP_SECRET", None)
    WHATSAPP_VERIFY_TOKEN: str = os.getenv("WHATSAPP_VERIFY_TOKEN", "eios_whatsapp_verify_token")
    WHATSAPP_API_VERSION: str = os.getenv("WHATSAPP_API_VERSION", "v18.0")

    def get_cors_origins_list(self) -> List[str]:
        origins = []
        if isinstance(self.CORS_ORIGINS, list):
            origins = self.CORS_ORIGINS
        elif isinstance(self.CORS_ORIGINS, str):
            origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        
        if self.FRONTEND_URL and self.FRONTEND_URL not in origins:
            origins.append(self.FRONTEND_URL)
        return origins

    model_config = SettingsConfigDict(
        env_file=[str(ENV_FILE_BACKEND), str(ENV_FILE_ROOT)],
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()