"""
200 ta lot tanlash: model prediction asosida stratified labeling.
"""

import os
import pandas as pd

DATA_DIR = "data"


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    feat_path = os.path.join(DATA_DIR, "lots_features.parquet")
    pred_path = os.path.join(DATA_DIR, "model_predictions.parquet")

    df = pd.read_parquet(feat_path)
    preds = pd.read_parquet(pred_path) if os.path.exists(pred_path) else pd.DataFrame()

    if not preds.empty:
        df = df.merge(preds[["lot_id", "ensemble_score", "xgb_prob", "iso_anomaly"]],
                      on="lot_id", how="left")

    cols = ["lot_id", "name", "start_price", "appraised_price", "region_code",
            "property_group", "is_closed", "auction_cnt", "is_single_step",
            "no_docs", "zaklad_percent", "price_vs_appraised", "duration_hours",
            "red_flag_score", "ensemble_score", "xgb_prob", "iso_anomaly", "url"]
    avail = [c for c in cols if c in df.columns]
    sub = df[avail].copy()

    # URL yaratish
    if "url" not in sub.columns:
        sub["url"] = "https://e-auksion.uz/lot-view?lot_id=" + df["lot_id"].astype(str)

    # Tanlash strategiyasi
    random_60 = sub.sample(60, random_state=42)
    exc = set(random_60["lot_id"])

    # Yuqori risk lotlar (red_flag_score > 5)
    high_risk = sub[~sub["lot_id"].isin(exc) & (sub.get("red_flag_score", 0) >= 5)]
    high_risk_70 = high_risk.sample(min(70, len(high_risk)), random_state=42)
    exc |= set(high_risk_70["lot_id"])

    # Model shubhalilari (ensemble_score > 0.6)
    if "ensemble_score" in sub.columns:
        suspicious = sub[~sub["lot_id"].isin(exc) & (sub["ensemble_score"] >= 0.6)]
        suspicious_70 = suspicious.sample(min(70, len(suspicious)), random_state=42)
    else:
        suspicious_70 = pd.DataFrame(columns=avail)

    labeled = pd.concat([random_60, high_risk_70, suspicious_70]).drop_duplicates("lot_id")
    labeled = labeled.sample(min(200, len(labeled)), random_state=42).reset_index(drop=True)

    labeled["is_suspicious"] = ""
    labeled["flag_type"] = ""
    labeled["comment"] = ""

    out_path = os.path.join(DATA_DIR, "red_flags_labeled_template.csv")
    labeled.to_csv(out_path, index=False, encoding="utf-8-sig")

    prog = (
        f"Jami: {len(labeled)} lot\n"
        f"  Random: {len(random_60)}\n"
        f"  Yuqori risk (score>=5): {len(high_risk_70)}\n"
        f"  Model shubhalisi: {len(suspicious_70)}\n\n"
        f"flag_type qiymatlari:\n"
        f"  normal\n"
        f"  price_below_appraised\n"
        f"  single_step_auction\n"
        f"  no_documents\n"
        f"  short_duration\n"
        f"  low_deposit\n"
        f"  price_outlier\n"
        f"  other\n\n"
        f"Ko'rsatma:\n"
        f"  1. url ustunidagi linkni brauzerda oching\n"
        f"  2. is_suspicious: 0 yoki 1\n"
        f"  3. flag_type: yuqoridagi ro'yxatdan\n"
        f"  4. Tugatgach red_flags_labeled.csv deb saqlang\n"
    )
    with open(os.path.join(DATA_DIR, "label_progress.txt"), "w", encoding="utf-8") as f:
        f.write(prog)

    print(f"Shablon: {out_path} ({len(labeled)} qator)")
    print(prog)


if __name__ == "__main__":
    main()
