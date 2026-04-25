"""
ML Model Training:
1. Isolation Forest — unsupervised anomaly detection
2. XGBoost — supervised (rule-based labels)
3. Model evaluation va feature importance

Ishlatish: python scripts/07_train.py
Natija:
    models/isolation_forest.pkl
    models/xgboost_model.pkl
    data/model_predictions.parquet
    data/feature_importance.csv
"""

import os
import pickle
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (average_precision_score, classification_report,
                               roc_auc_score)
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.preprocessing import StandardScaler
import xgboost as xgb

warnings.filterwarnings("ignore")

DATA_DIR = "data"
MODEL_DIR = "models"

# ML uchun feature guruhlar
NUMERIC_FEATURES = [
    "start_price_log",
    "appraised_price_log",
    "price_vs_appraised",
    "zaklad_ratio",
    "zaklad_percent",
    "step_percent",
    "auction_cnt",
    "auction_cnt_log",
    "view_count",
    "order_cnt",
    "images_count",
    "docs_count",
    "duration_hours",
    "start_hour",
    "start_weekday",
    "start_month",
    "seller_total_lots",
    "seller_avg_auction_cnt",
    "seller_no_docs_pct",
    "seller_closed_pct",
    "benchmark_price",
    "price_z_score",
    "regions_id",
    "exec_order_type_id",
    "lot_type",
]

BINARY_FEATURES = [
    "is_closed",
    "is_descending",
    "is_single_step",
    "price_below_appraised",
    "price_above_appraised",
    "high_views_no_orders",
    "no_docs",
    "no_images",
    "low_zaklad",
    "is_descending_closed",
    "is_short_duration",
    "is_very_short",
    "is_weekend",
    "seller_is_heavy",
    "price_outlier",
    "is_from_mib",
]


def prepare_features(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    all_feats = NUMERIC_FEATURES + BINARY_FEATURES
    avail = [f for f in all_feats if f in df.columns]
    X = df[avail].copy()
    # NaN -> median imputation
    for col in X.select_dtypes(include=[np.number]).columns:
        median = X[col].median()
        X[col] = X[col].fillna(median if pd.notna(median) else 0)
    return X, avail


def train_isolation_forest(X: pd.DataFrame, contamination: float = 0.15) -> IsolationForest:
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    clf = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        max_samples="auto",
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_scaled)
    clf._scaler = scaler
    return clf


def train_xgboost(X: pd.DataFrame, y: pd.Series) -> xgb.XGBClassifier:
    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=5,
        scale_pos_weight=(y == 0).sum() / (y == 1).sum(),
        use_label_encoder=False,
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X, y)
    return model


def plot_feature_importance(model: xgb.XGBClassifier, feature_names: list[str], out_path: str):
    importance = pd.Series(model.feature_importances_, index=feature_names)
    top20 = importance.nlargest(20).sort_values()

    fig, ax = plt.subplots(figsize=(10, 8))
    colors = ["#F44336" if "flag" in n or "risk" in n or "suspicious" in n else "#2196F3"
              for n in top20.index]
    top20.plot(kind="barh", ax=ax, color=colors)
    ax.set_title("Top 20 Feature Importance (XGBoost)", fontweight="bold", fontsize=13)
    ax.set_xlabel("Importance")
    plt.tight_layout()
    plt.savefig(out_path, bbox_inches="tight", dpi=120)
    plt.close()


def main():
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

    feat_path = os.path.join(DATA_DIR, "lots_features.parquet")
    df = pd.read_parquet(feat_path)
    print(f"Dataset: {len(df):,} lot, {len(df.columns)} ustun")

    X, feature_names = prepare_features(df)
    print(f"Feature matritsasi: {X.shape}")

    # ── 1. Isolation Forest (unsupervised) ────────────────────────────────
    print("\n[1] Isolation Forest o'qitilmoqda...")
    iso = train_isolation_forest(X)
    X_scaled = iso._scaler.transform(X)
    iso_scores = iso.score_samples(X_scaled)       # manfiy: -1 = anomaliya
    iso_labels = iso.predict(X_scaled)              # -1 = anomaliya, 1 = normal
    df["iso_score"] = -iso_scores                   # musbat: yuqori = shubhaliroq
    df["iso_anomaly"] = (iso_labels == -1).astype(int)
    print(f"   Anomaliya: {df['iso_anomaly'].sum():,} ({df['iso_anomaly'].mean()*100:.1f}%)")

    # ── 2. XGBoost (rule-based labels) ───────────────────────────────────
    print("\n[2] XGBoost o'qitilmoqda...")
    y = df["is_high_risk"].fillna(0).astype(int)
    pos_rate = y.mean()
    print(f"   Label taqsimlash: {y.value_counts().to_dict()} | pos={pos_rate*100:.1f}%")

    # Cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    xgb_model = train_xgboost(X, y)
    y_prob_cv = cross_val_predict(xgb_model, X, y, cv=cv, method="predict_proba")[:, 1]
    y_pred_cv = (y_prob_cv >= 0.5).astype(int)

    roc = roc_auc_score(y, y_prob_cv)
    ap = average_precision_score(y, y_prob_cv)
    print(f"   CV ROC-AUC: {roc:.4f} | Avg Precision: {ap:.4f}")

    # Final model (full data)
    xgb_final = train_xgboost(X, y)
    df["xgb_prob"] = xgb_final.predict_proba(X)[:, 1]
    df["xgb_pred"] = (df["xgb_prob"] >= 0.5).astype(int)

    # ── 3. Ensemble score ─────────────────────────────────────────────────
    from sklearn.preprocessing import MinMaxScaler
    mms = MinMaxScaler()
    iso_norm = mms.fit_transform(df[["iso_score"]]).ravel()
    df["ensemble_score"] = (iso_norm * 0.4 + df["xgb_prob"] * 0.6).round(4)
    df["is_suspicious"] = (df["ensemble_score"] >= 0.6).astype(int)
    print(f"\n[3] Ensemble: shubhali={df['is_suspicious'].sum():,} ({df['is_suspicious'].mean()*100:.1f}%)")

    # ── Model saqlash ─────────────────────────────────────────────────────
    with open(os.path.join(MODEL_DIR, "isolation_forest.pkl"), "wb") as f:
        pickle.dump(iso, f)
    with open(os.path.join(MODEL_DIR, "xgboost_model.pkl"), "wb") as f:
        pickle.dump(xgb_final, f)

    # ── Natijalar saqlash ─────────────────────────────────────────────────
    pred_cols = ["lot_id", "lot_number", "name", "start_price", "region_code",
                 "auction_type", "status", "auction_cnt", "red_flag_score",
                 "iso_score", "iso_anomaly", "xgb_prob", "ensemble_score", "is_suspicious",
                 "price_vs_appraised", "is_single_step", "no_docs", "duration_hours"]
    avail_pred = [c for c in pred_cols if c in df.columns]
    df[avail_pred].to_parquet(os.path.join(DATA_DIR, "model_predictions.parquet"), index=False)

    # ── Feature importance ────────────────────────────────────────────────
    fi = pd.Series(xgb_final.feature_importances_, index=feature_names)
    fi.sort_values(ascending=False).to_csv(
        os.path.join(DATA_DIR, "feature_importance.csv"), header=["importance"]
    )
    plot_feature_importance(
        xgb_final, feature_names, os.path.join(DATA_DIR, "feature_importance.png")
    )
    print(f"\nTop 10 feature:")
    print(fi.nlargest(10).round(4).to_string())

    # ── Summary ───────────────────────────────────────────────────────────
    summary = (
        f"Dataset: {len(df)} lot\n"
        f"Features: {len(feature_names)}\n"
        f"Isolation Forest anomaly: {df['iso_anomaly'].sum()} ({df['iso_anomaly'].mean()*100:.1f}%)\n"
        f"XGBoost CV ROC-AUC: {roc:.4f}\n"
        f"XGBoost CV Avg-Precision: {ap:.4f}\n"
        f"Ensemble suspicious: {df['is_suspicious'].sum()} ({df['is_suspicious'].mean()*100:.1f}%)\n"
    )
    with open(os.path.join(DATA_DIR, "model_summary.txt"), "w") as f:
        f.write(summary)
    print(f"\n{summary}")
    print("Modellar saqlandi:", MODEL_DIR)


if __name__ == "__main__":
    main()
