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


def get_session():
    with Session(engine) as session:
        yield session
