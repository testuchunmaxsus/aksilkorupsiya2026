"""Database engine + session helpers."""
import os
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session

# Allow override via DATABASE_URL env (Railway / Postgres / mounted volume)
_default_path = Path(__file__).parent.parent / "data" / "auksionwatch.db"
_default_path.parent.mkdir(parents=True, exist_ok=True)
DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite:///{_default_path}"

# SQLite-specific connect args; harmless to omit for Postgres
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


def init_db():
    from . import models  # noqa
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
