import sys
from pathlib import Path

# Ensure backend directory is in sys.path so app.* imports work from any cwd
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from fastapi import FastAPI, Depends, Request
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import logging
logger = logging.getLogger("agribridge")
logging.basicConfig(level=logging.INFO)


from .database.connection import get_db, engine, Base
from . import models
from .routes.auth import router as auth_router
from .routes.farmers import router as farmers_router
from .routes.buyers import router as buyers_router
from .routes.listings import router as listings_router
from .routes.orders import router as orders_router
from .routes.marketplace import router as marketplace_router
try:
    from .routes.ai import router as ai_router
except ImportError:
    ai_router = None  # AI route unavailable due to missing dependencies
from .routes.verifications import router as verifications_router
from .routes.recommendation import router as recommendation_router
from .routes.weather import router as weather_router
try:
    from .routes.voice import router as voice_router
except ImportError:
    voice_router = None  # Voice route unavailable due to missing dependencies
from .routes.crop_monitoring import router as crop_monitoring_router
from .routes.monitoring_v1 import router as monitoring_v1_router
from .routes.action_plans import router as action_plans_router
from .routes.orchestration import router as orchestration_router
from .routes.field_agent import router as field_agent_router, notification_router as tracked_notification_router
from .models.disease_record import DiseaseRecord


# Auto-create tables (users, otp_verifications, action_plans, plan_tasks, disease_records, etc.)
try:
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        columns_to_add = [
            ("action_plans", "crop_id", "VARCHAR(50) NULL"),
            ("action_plans", "state", "VARCHAR(100) NULL"),
            ("action_plans", "district", "VARCHAR(100) NULL"),
            ("action_plans", "village", "VARCHAR(100) NULL"),
            ("action_plans", "planting_date", "VARCHAR(50) NULL"),
            ("action_plans", "crop_stage", "VARCHAR(100) NULL"),
            ("action_plans", "risk_level", "VARCHAR(50) NOT NULL DEFAULT 'moderate'"),
            ("action_plans", "escalation_required", "TINYINT(1) NOT NULL DEFAULT 0"),
            ("action_plans", "escalation_reason", "TEXT NULL"),
            ("action_plans", "recommendation_json", "LONGTEXT NULL"),
            ("plan_tasks", "description", "TEXT NULL"),
            ("plan_tasks", "location", "VARCHAR(255) NULL"),
            ("plan_tasks", "execution_window", "VARCHAR(255) NULL"),
            ("disease_records", "inspection_status", "VARCHAR(50) NULL"),
            ("disease_records", "inspection_date", "DATETIME NULL"),
            ("disease_records", "farmer_notes", "TEXT NULL"),
            ("notification_events", "notification_type", "VARCHAR(50) NULL"),
            ("notification_events", "related_id", "INT NULL"),
            ("notification_events", "action_url", "VARCHAR(255) NULL"),
            ("notification_events", "meta_data", "TEXT NULL"),
        ]
        for tbl, col, col_type in columns_to_add:
            try:
                conn.execute(text(f"ALTER TABLE {tbl} ADD COLUMN {col} {col_type}"))
                conn.commit()
            except Exception:
                pass
except Exception as _e:
    pass


app = FastAPI(
    title="AgriBridge API",
    description="Backend API for the AgriBridge agricultural platform",
    version="1.0.1"
)

# Allows the frontend to be opened with a local static server during
# development while the API runs on FastAPI at http://127.0.0.1:8000.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================
# STARTUP EVENT — SAFE MODEL PRE-WARMING
# =========================================

import threading
try:
    from ..services.ai_service import initialize_ai
except ImportError:
    def initialize_ai():
        pass  # No-op when AI service unavailable

@app.on_event("startup")
def startup_event():
    """
    Safely triggers background pre-warming of active EfficientNet models
    so that judges experience instantaneous first inference without blocking
    initial application boot.
    """
    threading.Thread(target=initialize_ai, daemon=True).start()

# =========================================
# FRONTEND
# =========================================

BASE_DIR = Path(__file__).resolve().parents[2]

FRONTEND_DIR = BASE_DIR / "frontend"
UPLOADS_DIR = BASE_DIR / "uploads"


app.mount(
    "/frontend",
    StaticFiles(directory=FRONTEND_DIR),
    name="frontend"
)


# =========================================
# UPLOADS
# =========================================

app.mount(
    "/uploads",
    StaticFiles(directory=UPLOADS_DIR),
    name="uploads"
)


# =========================================
# API ROUTES
# =========================================

# Include API routers conditionally
app.include_router(auth_router)
app.include_router(farmers_router)
app.include_router(buyers_router)
app.include_router(listings_router)
app.include_router(orders_router)
app.include_router(marketplace_router)
if ai_router:
    app.include_router(ai_router)
app.include_router(verifications_router)
app.include_router(recommendation_router)
app.include_router(weather_router)
if voice_router:
    app.include_router(voice_router)
app.include_router(crop_monitoring_router)
app.include_router(monitoring_v1_router)
app.include_router(action_plans_router)
app.include_router(orchestration_router)
app.include_router(field_agent_router)
app.include_router(tracked_notification_router)




@app.get("/")
def root():
    index_file = FRONTEND_DIR / "pages" / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "success": True,
        "message": "AgriBridge Backend is running"
    }


@app.get("/api")
def api_root():
    return {
        "success": True,
        "message": "AgriBridge Backend is running"
    }


@app.get("/api/health")
def health_check():
    return {
        "success": True,
        "status": "healthy"
    }


# Global exception handler – catches unexpected errors and returns sanitized JSON response
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred while processing the request."
        },
    )

# DEBUG ONLY: temporary endpoint to trigger an unhandled exception for verification
@app.get("/debug/raise")
async def debug_raise():
    raise RuntimeError("Intentional error for middleware testing")


# =========================================
# LANGUAGES
# =========================================

@app.get("/api/languages/")
def get_supported_languages():
    """Return list of supported languages for the i18n system."""
    languages = {
        "en": "English",
        "hi": "हिन्दी",
        "mr": "मराठी",
        "bn": "বাংলা",
        "te": "తెలుగు",
        "ta": "தமிழ்",
        "kn": "ಕನ್ನಡ",
        "ml": "മലയാളം",
        "gu": "ગુજરાતી",
        "pa": "ਪੰਜਾਬੀ",
        "or": "ଓଡ଼ିଆ"
    }
    return {
        "success": True,
        "default_language": "en",
        "languages": languages
    }


@app.get("/api/db-test")
def database_test(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1")).scalar()

        return {
            "success": True,
            "database": "connected",
            "result": result
        }

    except Exception as e:
        return {
            "success": False,
            "database": "connection_failed",
            "error": str(e)
        }


@app.get("/api/db/status")
def get_db_status():
    """
    Operator/Admin database runtime visibility:
    Returns 'DATABASE: MySQL — ACTIVE' or 'DATABASE: SQLite FALLBACK — ACTIVE'.
    """
    from .database.connection import get_database_status
    return {
        "success": True,
        **get_database_status()
    }



@app.get("/api/db/tables")
def get_tables(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SHOW TABLES"))

        tables = [row[0] for row in result]

        return {
            "success": True,
            "tables": tables
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
        
@app.get("/api/db/databases")
def get_databases(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SHOW DATABASES"))

        databases = [row[0] for row in result]

        return {
            "success": True,
            "databases": databases
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
        
@app.get("/api/db/all-tables")
def get_all_tables(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("""
            SELECT TABLE_SCHEMA, TABLE_NAME
            FROM information_schema.tables
            WHERE TABLE_SCHEMA IN ('agribridge', 'agribridge_test')
            ORDER BY TABLE_SCHEMA, TABLE_NAME
        """))

        tables = [
            {
                "database": row[0],
                "table": row[1]
            }
            for row in result
        ]

        return {
            "success": True,
            "tables": tables
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
        
@app.get("/api/db/schema")
def get_database_schema(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("""
            SELECT
                TABLE_NAME,
                COLUMN_NAME,
                COLUMN_TYPE,
                IS_NULLABLE,
                COLUMN_KEY,
                COLUMN_DEFAULT,
                EXTRA
            FROM information_schema.columns
            WHERE TABLE_SCHEMA = DATABASE()
            ORDER BY TABLE_NAME, ORDINAL_POSITION
        """))

        schema = {}

        for row in result:
            table_name = row[0]

            if table_name not in schema:
                schema[table_name] = []

            schema[table_name].append({
                "column": row[1],
                "type": row[2],
                "nullable": row[3],
                "key": row[4],
                "default": row[5],
                "extra": row[6]
            })

        return {
            "success": True,
            "schema": schema
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# =========================================
# OPERATOR MAINTENANCE & CLEANUP
# =========================================

@app.post("/api/admin/cleanup-temp-uploads")
def trigger_cleanup(
    min_age_seconds: int = 900,
    dry_run: bool = False,
    db: Session = Depends(get_db)
):
    """
    Operator maintenance endpoint: Conservatively removes unreferenced scratch
    AI uploads while strictly preserving persistent database records.
    """
    try:
        from app.services.cleanup_service import cleanup_temporary_files
    except ImportError:
        from .services.cleanup_service import cleanup_temporary_files
    return cleanup_temporary_files(db=db, min_age_seconds=min_age_seconds, dry_run=dry_run)



