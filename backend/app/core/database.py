import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

db_url = settings.DATABASE_URL.strip()

# Normalize Heroku / Supabase / Render legacy postgres:// URLs to postgresql://
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# On Vercel ephemeral serverless filesystem, redirect default SQLite path to /tmp/eios.db if PostgreSQL is unconfigured
if os.getenv("VERCEL") and db_url.startswith("sqlite"):
    db_url = "sqlite:////tmp/eios.db"

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
