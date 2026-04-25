"""Database engine + session helpers — works with SQLite and Postgres.

Bu modul backend'ning DB ulanish nuqtasi. Ikkita rejimda ishlaydi:
  - Lokal develop: SQLite (data/auksionwatch.db)
  - Production (Railway): Postgres — DATABASE_URL env orqali
"""
import os
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session


def _resolve_database_url() -> str:
    """DATABASE_URL ni env'dan oladi va Railway formatini SQLAlchemy formatiga moslaydi.

    Tartib:
      1. DATABASE_URL env mavjud bo'lsa — uni ishlatadi (Railway/Heroku)
      2. Aks holda — lokal SQLite (data/auksionwatch.db)
    """
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        # Railway/Heroku 'postgres://' formatida beradi, SQLAlchemy 1.4+ 'postgresql://' kutadi.
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://"):]
        # psycopg2 driverini aniq belgilash (psycopg3 ham o'rnatilgan bo'lsa noaniqlikni oldini oladi)
        if url.startswith("postgresql://") and "+psycopg" not in url:
            url = "postgresql+psycopg2://" + url[len("postgresql://"):]
        return url

    # Lokal SQLite fallback — data/auksionwatch.db
    default_path = Path(__file__).parent.parent / "data" / "auksionwatch.db"
    default_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{default_path}"


# Modulning yuqorisida bir marta hisoblanadi
DATABASE_URL = _resolve_database_url()
IS_SQLITE = DATABASE_URL.startswith("sqlite")

# SQLite uchun threading argumenti — Postgres'da kerakmas
connect_args = {"check_same_thread": False} if IS_SQLITE else {}

# Postgres uchun pool sozlamalari — Railway proxy idle timeout'ni yengish uchun
engine_kwargs: dict = {"echo": False, "connect_args": connect_args}
if not IS_SQLITE:
    engine_kwargs.update(
        pool_pre_ping=True,    # har query oldidan ulanishni tekshirish
        pool_recycle=300,      # 5 daqiqada bir ulanishni qayta yaratish
        pool_size=5,
        max_overflow=5,
    )

# Bitta global engine — barcha modul'lar shuni ishlatadi
engine = create_engine(DATABASE_URL, **engine_kwargs)


def init_db() -> None:
    """Jadvallarni yaratish + yangi ustunlar uchun migration ishga tushirish."""
    from . import models  # noqa: F401  — SQLModel jadvallarni ro'yxatga oladi
    SQLModel.metadata.create_all(engine)  # mavjud jadvallarni yaratadi (lekin alter qilmaydi)
    _ensure_columns()                     # qo'shimcha ustunlar uchun ALTER TABLE


# Idempotent migration — `lot` jadvaliga yangi ustunlar qo'shadi.
# SQLAlchemy `create_all` mavjud jadvalga ustun qo'shmaydi — shuning uchun bu funksiya kerak.
_REQUIRED_COLUMNS: list[tuple[str, str, str]] = [
    # (ustun_nomi, SQLite turi, Postgres turi)
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
    """Mavjud jadvalga yetishmayotgan ustunlarni qo'shish (idempotent ALTER TABLE)."""
    from sqlalchemy import inspect, text
    try:
        inspector = inspect(engine)
        if "lot" not in inspector.get_table_names():
            return  # create_all hali yaratmagan — ustunlar to'liq

        # Mavjud ustunlar to'plami
        existing = {c["name"] for c in inspector.get_columns("lot")}

        # Har bir kerakli ustunni tekshirib, yo'q bo'lsa qo'shish
        with engine.begin() as conn:
            for col, sqlite_type, pg_type in _REQUIRED_COLUMNS:
                if col in existing:
                    continue
                col_type = sqlite_type if IS_SQLITE else pg_type
                conn.execute(text(f'ALTER TABLE lot ADD COLUMN {col} {col_type}'))
                print(f"[migrate] added column lot.{col} {col_type}", flush=True)

            # Indekslar — idempotent (CREATE INDEX IF NOT EXISTS)
            try:
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lot_seller_id ON lot(seller_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lot_ml_score ON lot(ml_score)"))
            except Exception as ix_e:
                print(f"[migrate] index warning: {ix_e}", flush=True)
    except Exception as e:
        # Migration xatosi production'da silent fail bo'lsin (loglanadi, lekin app'ni to'xtatmaydi)
        print(f"[migrate] skipped: {e}", flush=True)


def get_session():
    """FastAPI dependency — har request uchun yangi DB session beradi."""
    with Session(engine) as session:
        yield session
