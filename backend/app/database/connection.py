import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

_env_path = Path(__file__).resolve().parents[2] / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path)
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "agribridge_test")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

Base = declarative_base()

# ------------------------------------------------------------------------------
# DATABASE CONNECTION INITIALIZATION WITH VISIBLE STARTUP BANNER
# ------------------------------------------------------------------------------

def _init_database():
    mysql_url = URL.create(
        "mysql+pymysql",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=int(DB_PORT),
        database=DB_NAME,
    )

    try:
        mysql_engine = create_engine(
            mysql_url,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 3}
        )
        # Test connection immediately
        with mysql_engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        print("\n" + "=" * 50)
        print(f"DATABASE: Connected to MySQL at {DB_HOST}:{DB_PORT}/{DB_NAME}")
        print("=" * 50 + "\n", flush=True)

        return mysql_engine

    except Exception as err:
        sqlite_path = Path(__file__).resolve().parents[3] / "backend" / "agribridge.db"
        sqlite_engine = create_engine(
            f"sqlite:///{sqlite_path}",
            connect_args={"check_same_thread": False}
        )

        print("\n" + "=" * 60, file=sys.stderr)
        print("WARNING: MySQL connection FAILED. Falling back to local SQLite (agribridge.db).", file=sys.stderr)
        print("WARNING: This is NOT your production data. Start MySQL before demoing.", file=sys.stderr)
        print("=" * 60 + "\n", file=sys.stderr, flush=True)

        return sqlite_engine


engine = _init_database()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_database_status() -> dict:
    """
    Returns runtime database visibility for the operator and dashboards
    without exposing any passwords or sensitive credentials.
    """
    dialect = engine.dialect.name
    is_sqlite = (dialect == "sqlite")
    status_label = "DATABASE:\nSQLite FALLBACK — ACTIVE" if is_sqlite else "DATABASE:\nMySQL — ACTIVE"
    single_line = "SQLite FALLBACK — ACTIVE" if is_sqlite else "MySQL — ACTIVE"

    return {
        "status": single_line,
        "status_label": status_label,
        "dialect": dialect,
        "is_fallback": is_sqlite,
        "database_name": "agribridge.db" if is_sqlite else os.getenv("DB_NAME", "agribridge_test"),
        "warning": (
            "CRITICAL OPERATOR WARNING: Local SQLite fallback is active! MySQL connection is down. "
            "Do not present demo believing data is in MySQL."
            if is_sqlite else None
        )
    }
