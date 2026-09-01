import logging
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings
from app.core.database import engine, Base, get_db
from database.seeds.seed_data import seed_database

logger = logging.getLogger("eios_app")

# API Routers
from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.customers import router as customers_router
from app.api.projects import router as projects_router
from app.api.payments import router as payments_router
from app.api.tasks import router as tasks_router
from app.api.approvals import router as approvals_router
from app.api.connectors import router as connectors_router
from app.api.ai import router as ai_router
from app.api.activity_logs import router as activity_logs_router
from app.api.settings import router as settings_router

# Initialize database tables safely without crashing startup if DB is offline
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    logger.warning(f"Database table initialization warning: {e}")

# Seed initial data ONLY in development environment when database is empty
if settings.ENVIRONMENT.lower() != "production":
    try:
        seed_database()
    except Exception as e:
        logger.info(f"Seed initialization note: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="EIOS — AI COO Business Operations Platform API",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT.lower() != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT.lower() != "production" else None
)

# Configurable Production CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled server exception on {request.url.path}: {exc}")
    if settings.ENVIRONMENT.lower() == "production":
        message = "An internal server error occurred. Please contact system administrator."
    else:
        message = str(exc)

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": message
            }
        }
    )

# Router Registration
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(dashboard_router, prefix=settings.API_V1_STR)
app.include_router(customers_router, prefix=settings.API_V1_STR)
app.include_router(projects_router, prefix=settings.API_V1_STR)
app.include_router(payments_router, prefix=settings.API_V1_STR)
app.include_router(tasks_router, prefix=settings.API_V1_STR)
app.include_router(approvals_router, prefix=settings.API_V1_STR)
app.include_router(connectors_router, prefix=settings.API_V1_STR)
app.include_router(ai_router, prefix=settings.API_V1_STR)
app.include_router(activity_logs_router, prefix=settings.API_V1_STR)
app.include_router(settings_router, prefix=settings.API_V1_STR)

# --- Health Endpoints ---

@app.get("/")
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "app": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0"
    }

@app.get("/health/db")
def db_health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "database": "connected",
            "environment": settings.ENVIRONMENT
        }
    except Exception as e:
        logger.error(f"Database readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "database": "disconnected",
                "error": str(e) if settings.ENVIRONMENT.lower() != "production" else "Database connection failed"
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
