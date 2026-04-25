"""
3 qadam:
  1. Fergana.xlsx dan weak-supervision yorliqlar yaratish (200 lot)
  2. XGBoost qayta train (real feature'lar bilan)
  3. Modelni saqlash → core_pipeline.py ishlatadi

Ishlatish: python scripts/09_label_and_train.py
"""

import os
import sys
import pickle
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.metrics import roc_auc_score, average_precision_score

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.core_pipeline import load_file, clean, add_features, ML_FEATURES

DATA_DIR  = "data"
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)


# ─── 1. YUKLASH VA FEATURE'LAR ───────────────────────────────────────────────

sys.stderr.write("1. Fergana.xlsx yuklanmoqda...\n")
df = load_file("data/Fergana.xlsx")
df = clean(df)
df = add_features(df)
sys.stderr.write(f"   {len(df)} lot\n")


# ─── 2. WEAK-SUPERVISION YORLIQLASH ─────────────────────────────────────────
# Kuchli signallar → yuqori ishonch bilan yorliq qo'yiladi.
# Noaniq holatlar o'tkazib yuboriladi (faqat aniq holatlar olinadi).

def label_lot(row) -> int:
    """
    1  = shubhali (suspicious)
    0  = normal
    -1 = noaniq (training'ga kirmaydi)
    """
    ac    = int(row.get("auction_count", 1))
    ratio = row.get("price_ratio", np.nan)
    bankrupt    = int(row.get("is_bankruptcy", 0))
    no_disc     = int(row.get("no_discount", 0))
    below10     = int(row.get("price_below_10pct", 0))
    below70     = int(row.get("price_below_70pct", 0))
    ultra_rep   = int(row.get("is_ultra_repeated", 0))  # >100
    mega_rep    = int(row.get("is_mega_repeated", 0))   # >50
    seller_cnt  = int(row.get("seller_lot_count", 1))

    # ── ANIQ SHUBHALI (is_suspicious=1) ─────────────────────────────────
    # Bankrotlik + chegirmasiz: klassik korrupsiya belgisi
    if bankrupt and no_disc:
        return 1
    # Narx baholashning 10% dan past + ko'p marta e'lon
    if below10 and ac > 5:
        return 1
    # 100+ marta e'lon + chegirmasiz yoki juda past narx
    if ultra_rep and (no_disc or below10):
        return 1
    # 50+ marta + narx 10% dan past
    if mega_rep and below10:
        return 1
    # Bir sotuvchi 100+ lot + past narx
    if seller_cnt >= 100 and below70:
        return 1

    # ── ANIQ NORMAL (is_suspicious=0) ───────────────────────────────────
    # 1 marta e'lon + chegirma bor (0.3 - 0.95) + bankrot emas
    if (ac == 1 and pd.notna(ratio)
            and 0.30 <= ratio <= 0.95
            and not bankrupt):
        return 0
    # 2-3 marta e'lon + normal narx
    if (ac <= 3 and pd.notna(ratio)
            and 0.40 <= ratio <= 0.90
            and not bankrupt and not below70):
        return 0

    return -1  # noaniq — o'tkazib yuboriladi


df["is_suspicious"] = df.apply(label_lot, axis=1)

labeled = df[df["is_suspicious"] != -1].copy()
suspicious_df = labeled[labeled["is_suspicious"] == 1]
normal_df     = labeled[labeled["is_suspicious"] == 0]

sys.stderr.write(f"   Shubhali (1): {len(suspicious_df)}\n")
sys.stderr.write(f"   Normal   (0): {len(normal_df)}\n")

# Balansli namuna: 100 shubhali + 100 normal (yoki mavjud minimum)
n_each = min(100, len(suspicious_df), len(normal_df))
sample = pd.concat([
    suspicious_df.sample(n_each, random_state=42),
    normal_df.sample(n_each, random_state=42),
]).reset_index(drop=True)

sys.stderr.write(f"   Training sample: {len(sample)} lot ({n_each} + {n_each})\n")

# Labeled CSV saqlash
label_cols = [
    "lot_number", "lot_url", "district", "category", "auction_settings",
    "start_price", "appraised_price", "price_ratio", "auction_count",
    "is_suspicious", "is_bankruptcy", "no_discount", "price_below_10pct",
    "price_below_70pct", "is_ultra_repeated", "seller_lot_count",
]
avail = [c for c in label_cols if c in sample.columns]
sample[avail].to_csv(
    os.path.join(DATA_DIR, "red_flags_labeled.csv"),
    index=False, encoding="utf-8-sig",
)
sys.stderr.write("   red_flags_labeled.csv saqlandi\n")


# ─── 3. FEATURE MATRIX ───────────────────────────────────────────────────────

feats = [f for f in ML_FEATURES if f in sample.columns]
X = sample[feats].copy()
y = sample["is_suspicious"].astype(int)

for col in X.columns:
    X[col] = pd.to_numeric(X[col], errors="coerce")
    X[col] = X[col].fillna(X[col].median() if X[col].notna().any() else 0)

scaler  = StandardScaler()
X_scaled = scaler.fit_transform(X)


# ─── 4. ISOLATION FOREST (unsupervised) ─────────────────────────────────────

sys.stderr.write("\n2. Isolation Forest train...\n")
iso = IsolationForest(
    n_estimators=200,
    contamination=0.12,
    max_samples="auto",
    random_state=42,
    n_jobs=-1,
)
iso.fit(X_scaled)

# Validation: labeled ma'lumotlarda qanchalik aniqlaydi
iso_preds = iso.predict(X_scaled)          # -1 = anomaly, 1 = normal
iso_binary = (iso_preds == -1).astype(int) # 1 = anomaly
iso_auc = roc_auc_score(y, -iso.score_samples(X_scaled))
sys.stderr.write(f"   IsolationForest ROC-AUC (labeled): {iso_auc:.3f}\n")

with open(os.path.join(MODEL_DIR, "isolation_forest.pkl"), "wb") as f:
    pickle.dump({"model": iso, "scaler": scaler, "features": feats}, f)
sys.stderr.write("   models/isolation_forest.pkl saqlandi\n")


# ─── 5. XGBOOST (supervised) ─────────────────────────────────────────────────

sys.stderr.write("\n3. XGBoost train...\n")
try:
    from xgboost import XGBClassifier

    pos_weight = (y == 0).sum() / max((y == 1).sum(), 1)
    xgb = XGBClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=float(pos_weight),
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1,
        verbosity=0,
    )

    # Cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_results = cross_validate(
        xgb, X_scaled, y, cv=cv,
        scoring=["roc_auc", "average_precision"],
        return_train_score=False,
    )
    auc_mean = cv_results["test_roc_auc"].mean()
    ap_mean  = cv_results["test_average_precision"].mean()
    sys.stderr.write(f"   CV ROC-AUC:        {auc_mean:.3f} (+/- {cv_results['test_roc_auc'].std():.3f})\n")
    sys.stderr.write(f"   CV Avg-Precision:  {ap_mean:.3f}\n")

    # To'liq dataset'da train
    xgb.fit(X_scaled, y)

    # Feature importance
    importance = pd.Series(xgb.feature_importances_, index=feats).sort_values(ascending=False)
    sys.stderr.write("\n   Top 10 muhim feature:\n")
    for feat, imp in importance.head(10).items():
        sys.stderr.write(f"     {feat:<35} {imp:.4f}\n")

    importance.to_csv(os.path.join(DATA_DIR, "feature_importance.csv"))

    with open(os.path.join(MODEL_DIR, "xgboost_model.pkl"), "wb") as f:
        pickle.dump({
            "model":    xgb,
            "scaler":   scaler,
            "features": feats,
            "cv_auc":   float(auc_mean),
            "cv_ap":    float(ap_mean),
        }, f)
    sys.stderr.write("   models/xgboost_model.pkl saqlandi\n")

    # Model summary
    summary = (
        f"Training data: Fergana.xlsx (weak-supervision)\n"
        f"Sample: {n_each} shubhali + {n_each} normal = {len(sample)} lot\n"
        f"Features: {len(feats)}\n"
        f"IsolationForest ROC-AUC (labeled): {iso_auc:.3f}\n"
        f"XGBoost CV ROC-AUC: {auc_mean:.3f} (+/- {cv_results['test_roc_auc'].std():.3f})\n"
        f"XGBoost CV Avg-Precision: {ap_mean:.3f}\n"
        f"\nTop features:\n"
    )
    for feat, imp in importance.head(15).items():
        summary += f"  {feat:<35} {imp:.4f}\n"

    with open(os.path.join(DATA_DIR, "model_summary.txt"), "w", encoding="utf-8") as f:
        f.write(summary)

    XGB_AVAILABLE = True

except ImportError:
    sys.stderr.write("   XGBoost o'rnatilmagan. pip install xgboost\n")
    XGB_AVAILABLE = False


# ─── 6. YAKUNIY HISOBOT ──────────────────────────────────────────────────────

sys.stderr.write("\n" + "=" * 50 + "\n")
sys.stderr.write("TAYYOR:\n")
sys.stderr.write(f"  data/red_flags_labeled.csv  ({len(sample)} lot)\n")
sys.stderr.write(f"  models/isolation_forest.pkl\n")
if XGB_AVAILABLE:
    sys.stderr.write(f"  models/xgboost_model.pkl    (AUC={auc_mean:.3f})\n")
sys.stderr.write("=" * 50 + "\n")
