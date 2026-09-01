import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

logger = logging.getLogger("eios_database")

def get_sanitized_db_url() -> str:
    raw_url = (settings.DATABASE_URL or "").strip().strip("'").strip('"')
    
    if not raw_url:
        raw_url = "sqlite:///./eios.db"

    # Normalize Heroku / Supabase / Render / Neon legacy postgres:// URLs to postgresql://
    if raw_url.startswith("postgres://"):
        raw_url = raw_url.replace("postgres://", "postgresql://", 1)

    # On Vercel ephemeral serverless filesystem, if default SQLite is used, fallback to /tmp/eios.db
    if os.getenv("VERCEL") and raw_url.startswith("sqlite"):
        raw_url = "sqlite:////tmp/eios.db"

    # Validate URL parsing with SQLAlchemy make_url
    try:
        make_url(raw_url)
    except Exception as parse_err:
        logger.error(f"SQLAlchemy failed to parse DATABASE_URL: {parse_err}")
        if os.getenv("VERCEL"):
            raw_url = "sqlite:////tmp/eios.db"
        else:
            raw_url = "sqlite:///./eios.db"

    return raw_url

db_url = get_sanitized_db_url()

connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=3600 if not db_url.startswith("sqlite") else -1
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
