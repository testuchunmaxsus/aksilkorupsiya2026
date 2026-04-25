"""Run ML pipeline on Fergana.xlsx and import predictions into Lot table.

Combines:
  - rule_score (40%)
  - xgb_prob (35%, XGBoost classifier)
  - iso_norm (25%, IsolationForest anomaly)

XGBoost CV AUC = 0.98 (trained on weak-supervised 114 lot from Fergana).
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ml"))

# core_pipeline.py expects models/ to be relative to cwd; switch dir
ML_DIR = ROOT / "ml"


def main():
    import pandas as pd
    from sqlmodel import Session, select, func
    from backend.db import engine
    from backend.models import Lot

    # core_pipeline imports relative paths — chdir into ml/
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
        os.chdir(cwd)

    preds: pd.DataFrame = result["predictions"]
    print(f"\n[ml] {len(preds)} predictions ready")

    # Map to lot_id; join into DB
    preds["lot_id"] = pd.to_numeric(preds["lot_number"], errors="coerce").astype("Int64")
    preds = preds.dropna(subset=["lot_id"])

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

    print(f"[ml] joining to {len(by_id)} lots...")
    updated = 0
    not_found = 0
    with Session(engine) as session:
        for lot_id, ml in by_id.items():
            lot = session.get(Lot, lot_id)
            if not lot:
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
