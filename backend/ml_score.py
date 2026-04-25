"""ML pipeline'ni Fergana.xlsx ustida ishlatib, natijalarni Lot jadvaliga yozish.

ML chining ishi (ml/scripts/core_pipeline.py):
  - 33 feature engineering
  - Rule score (40%)
  - XGBoost probability (35%) — CV AUC 0.98
  - IsolationForest anomaly (25%)
  - Ensemble final score 0-1 + KRITIK/YUQORI/O'RTA/PAST level

Bu skript shu pipeline'ni chaqiradi va lot_id bo'yicha bizning Lot
jadvaliga ml_score, ml_level, ml_reason, xgb_prob, iso_score yozadi.
Natijada bizning rule-based engine va ML ensemble lot detail'da
side-by-side ko'rinadi.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ml"))

# core_pipeline.py models/ ni cwd'ga nisbatan o'qiydi → ml/ ga chdir kerak
ML_DIR = ROOT / "ml"


def main():
    import pandas as pd
    from sqlmodel import Session, select, func
    from backend.db import engine
    from backend.models import Lot

    # ML pipeline'ni ml/ ichida ishga tushirish (relative path'lar uchun)
    cwd = os.getcwd()
    os.chdir(ML_DIR)
    try:
        from scripts.core_pipeline import run_pipeline
        result = run_pipeline(
            input_path=str(ML_DIR / "data" / "Fergana.xlsx"),
            output_dir=str(ROOT / "data" / "ml_output"),
            verbose=True,
        )
    finally:
        os.chdir(cwd)  # original cwd'ni qaytarish

    preds: pd.DataFrame = result["predictions"]
    print(f"\n[ml] {len(preds)} predictions ready")

    # lot_number → lot_id (integer) — bizning DB'da lot.id bilan join
    preds["lot_id"] = pd.to_numeric(preds["lot_number"], errors="coerce").astype("Int64")
    preds = preds.dropna(subset=["lot_id"])

    # DataFrame → dict tezkor lookup uchun
    by_id: dict[int, dict] = {
        int(r.lot_id): {
            "ml_score": float(r.risk_score) if pd.notna(r.risk_score) else None,
            "ml_level": r.risk_level if pd.notna(r.risk_level) else None,
            "ml_reason": str(r.why_flagged) if pd.notna(r.why_flagged) else None,
            "ml_xgb_prob": float(r.xgb_prob) if pd.notna(r.xgb_prob) else None,
            "ml_iso_score": float(r.iso_score) if pd.notna(r.iso_score) else None,
        }
        for r in preds.itertuples()
    }

    # DB'ga yozish — har 1000 lot dan keyin commit
    print(f"[ml] joining to {len(by_id)} lots...")
    updated = 0
    not_found = 0
    with Session(engine) as session:
        for lot_id, ml in by_id.items():
            lot = session.get(Lot, lot_id)
            if not lot:
                # Lot DB'da yo'q — ML predictions ortiqcha (skip)
                not_found += 1
                continue
            for k, v in ml.items():
                setattr(lot, k, v)
            updated += 1
            if updated % 1000 == 0:
                session.commit()
                print(f"  updated {updated}...")
        session.commit()

    print(f"[ml] DONE — updated {updated}, not in DB {not_found}")

    # Yakuniy stat
    with Session(engine) as session:
        n_with_ml = session.exec(
            select(func.count(Lot.id)).where(Lot.ml_score.is_not(None))
        ).one()
        kritik = session.exec(
            select(func.count(Lot.id)).where(Lot.ml_level == "KRITIK")
        ).one()
        print(f"[db] lots with ML score: {n_with_ml}, KRITIK: {kritik}")


if __name__ == "__main__":
    main()
