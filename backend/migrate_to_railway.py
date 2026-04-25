"""Bulk-migrate local SQLite Lot rows into Railway Postgres.

Usage (run locally, NOT inside Railway container):
    python -m backend.migrate_to_railway "postgresql://postgres:PASS@metro.proxy.rlwy.net:25130/railway"

Or set RAILWAY_DATABASE_URL env and just run without args.

Reads from data/auksionwatch.db (local SQLite) and inserts/updates rows in
Railway Postgres via SQLAlchemy ORM (type-safe).
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlmodel import Session, SQLModel, create_engine, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from backend.models import Lot

LOCAL_DB = ROOT / "data" / "auksionwatch.db"
BATCH = 500


def main():
    target_url = (
        (sys.argv[1] if len(sys.argv) > 1 else "")
        or os.getenv("RAILWAY_DATABASE_URL", "")
        or os.getenv("DATABASE_PUBLIC_URL", "")
        or os.getenv("DATABASE_URL", "")
    ).strip()
    if not target_url:
        print(
            "ERROR: no Postgres URL provided.\n"
            "  Run: railway service link Postgres\n"
            "       railway run python -m backend.migrate_to_railway",
            file=sys.stderr,
        )
        sys.exit(1)
    if target_url.startswith("postgres://"):
        target_url = "postgresql://" + target_url[len("postgres://"):]
    if target_url.startswith("postgresql://") and "+psycopg" not in target_url:
        target_url = "postgresql+psycopg2://" + target_url[len("postgresql://"):]

    print(f"[migrate] source: {LOCAL_DB}")
    print(f"[migrate] target: {target_url.split('@')[-1][:50]}")

    src = create_engine(f"sqlite:///{LOCAL_DB}", connect_args={"check_same_thread": False})
    dst = create_engine(
        target_url,
        pool_pre_ping=True,
        pool_recycle=300,
    )

    print("[migrate] ensuring target schema...")
    SQLModel.metadata.create_all(dst)
    # Reuse the same idempotent migration as backend
    from backend.db import _ensure_columns, IS_SQLITE  # noqa
    # _ensure_columns reads from `engine` global — re-bind it temporarily
    import backend.db as _db
    saved_engine = _db.engine
    saved_is_sqlite = _db.IS_SQLITE
    _db.engine = dst
    _db.IS_SQLITE = False
    try:
        _db._ensure_columns()
    finally:
        _db.engine = saved_engine
        _db.IS_SQLITE = saved_is_sqlite

    print("[migrate] reading local rows...")
    with Session(src) as s:
        rows = s.exec(select(Lot)).all()
    total = len(rows)
    print(f"[migrate] {total} lots to upload")
    if total == 0:
        print("[migrate] nothing to migrate")
        return

    written = 0
    table = Lot.__table__
    with dst.begin() as conn:
        for i in range(0, total, BATCH):
            batch = rows[i : i + BATCH]
            payload = []
            for r in batch:
                d = r.model_dump()
                payload.append(d)
            stmt = pg_insert(table).values(payload)
            # Upsert on primary key (id)
            update_cols = {c.name: stmt.excluded[c.name] for c in table.columns if c.name != "id"}
            stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=update_cols)
            conn.execute(stmt)
            written += len(batch)
            print(f"[migrate] {written}/{total} ({written/total*100:.0f}%)", flush=True)

    print(f"[migrate] DONE — {written} rows upserted")
    with Session(dst) as s:
        from sqlmodel import func
        n = s.exec(select(func.count(Lot.id))).one()
        kritik = s.exec(select(func.count(Lot.id)).where(Lot.ml_level == "KRITIK")).one()
        high = s.exec(select(func.count(Lot.id)).where(Lot.risk_level == "high")).one()
        print(f"[target] total: {n}, ML KRITIK: {kritik}, rule high: {high}")


if __name__ == "__main__":
    main()
