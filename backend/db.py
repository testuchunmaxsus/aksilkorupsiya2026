"""Database engine + session helpers — works with SQLite and Postgres."""
import os
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session


def _resolve_database_url() -> str:
    """Pick DATABASE_URL from env, normalize Railway/Heroku 'postgres://' to 'postgresql://'.

    Fallbacks:
      1. DATABASE_URL env (Railway, Heroku, local override)
      2. Local SQLite at data/auksionwatch.db
    """
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        # Railway/Heroku still emit `postgres://`; SQLAlchemy 1.4+ requires `postgresql://`.
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://"):]
        # psycopg2 explicit driver hint (avoids ambiguity with psycopg3 if both installed)
        if url.startswith("postgresql://") and "+psycopg" not in url:
            url = "postgresql+psycopg2://" + url[len("postgresql://"):]
        return url

    default_path = Path(__file__).parent.parent / "data" / "auksionwatch.db"
    default_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{default_path}"


DATABASE_URL = _resolve_database_url()
IS_SQLITE = DATABASE_URL.startswith("sqlite")

# SQLite-specific connect args; harmless to omit for Postgres.
connect_args = {"check_same_thread": False} if IS_SQLITE else {}

# Postgres benefits from a small pool + recycle to handle Railway proxy idle timeouts.
engine_kwargs: dict = {"echo": False, "connect_args": connect_args}
if not IS_SQLITE:
    engine_kwargs.update(
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=5,
        max_overflow=5,
    )

engine = create_engine(DATABASE_URL, **engine_kwargs)


def init_db() -> None:
    from . import models  # noqa: F401  — register tables
    SQLModel.metadata.create_all(engine)
    _ensure_columns()


# Lightweight idempotent migration — adds new columns to an existing `lot` table
# without breaking SQLite/Postgres-native behaviour. SQLAlchemy `create_all` does
# not alter existing tables, so we run targeted `ALTER TABLE ADD COLUMN IF NOT EXISTS`.
_REQUIRED_COLUMNS: list[tuple[str, str, str]] = [
    # (column_name, sqlite_type, postgres_type)
    ("appraised_price", "REAL", "DOUBLE PRECISION"),
    ("times_auctioned", "INTEGER", "INTEGER"),
    ("seller_name", "TEXT", "TEXT"),
    ("seller_id", "INTEGER", "BIGINT"),
    ("is_descending", "BOOLEAN", "BOOLEAN"),
    ("categories", "JSON", "JSONB"),
    ("ml_score", "REAL", "DOUBLE PRECISION"),
    ("ml_level", "TEXT", "TEXT"),
    ("ml_reason", "TEXT", "TEXT"),
    ("ml_xgb_prob", "REAL", "DOUBLE PRECISION"),
    ("ml_iso_score", "REAL", "DOUBLE PRECISION"),
]


def _ensure_columns() -> None:
    """Idempotent ALTER TABLE migration for evolving Lot schema."""
    from sqlalchemy import inspect, text
    try:
        inspector = inspect(engine)
        if "lot" not in inspector.get_table_names():
            return  # create_all just made it — already has all columns
        existing = {c["name"] for c in inspector.get_columns("lot")}
        with engine.begin() as conn:
            for col, sqlite_type, pg_type in _REQUIRED_COLUMNS:
                if col in existing:
                    continue
                col_type = sqlite_type if IS_SQLITE else pg_type
                conn.execute(text(f'ALTER TABLE lot ADD COLUMN {col} {col_type}'))
                print(f"[migrate] added column lot.{col} {col_type}", flush=True)
            # Indexes (idempotent)
            try:
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lot_seller_id ON lot(seller_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lot_ml_score ON lot(ml_score)"))
            except Exception as ix_e:
                print(f"[migrate] index warning: {ix_e}", flush=True)
    except Exception as e:
        print(f"[migrate] skipped: {e}", flush=True)


def get_session():
    with Session(engine) as session:
        yield session
