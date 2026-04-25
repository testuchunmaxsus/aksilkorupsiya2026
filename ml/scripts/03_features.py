"""
Qadam 5: ML feature engineering.
Ishlatish: python scripts/03_features.py
"""

import os
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
DATA_DIR = "data"


def add_price_features(df: pd.DataFrame) -> pd.DataFrame:
    # Baholangan narx vs boshlanish narxi
    df["price_vs_appraised"] = np.where(
        (df["appraised_price"] > 0) & df["appraised_price"].notna(),
        df["start_price"] / df["appraised_price"],
        np.nan,
    )
    # Zaklad nisbati
    df["zaklad_ratio"] = df["zaklad_summa"] / df["start_price"].replace(0, np.nan)

    # Log narx
    df["start_price_log"] = np.log1p(df["start_price"].fillna(0))
    df["appraised_price_log"] = np.log1p(df["appraised_price"].fillna(0))

    # Narx past baholangan (start < 70% appraised = shubhali)
    df["price_below_appraised"] = (
        (df["price_vs_appraised"] < 0.7) & df["price_vs_appraised"].notna()
    ).astype("Int8")

    # Narx yuqori baholangan (start > 130% appraised = shubhali boshqa tomon)
    df["price_above_appraised"] = (
        (df["price_vs_appraised"] > 1.3) & df["price_vs_appraised"].notna()
    ).astype("Int8")
    return df


def add_auction_features(df: pd.DataFrame) -> pd.DataFrame:
    df["is_closed"] = df["is_closed"].fillna(0).astype(int)
    df["is_descending"] = df["is_descending"].fillna(0).astype(int)

    # Kam raqobat: auction_cnt = 1 (faqat bitta qadam)
    df["is_single_step"] = (df["auction_cnt"] == 1).astype("Int8")
    df["auction_cnt_log"] = np.log1p(df["auction_cnt"].fillna(0))

    # Juda ko'p ko'rishlar bor lekin ariza yo'q (shubhali)
    df["high_views_no_orders"] = (
        (df["view_count"] > 100) & (df["order_cnt"] == 0)
    ).astype("Int8")

    df["docs_count"] = df["docs_count"].fillna(0)
    df["images_count"] = df["images_count"].fillna(0)

    # Hujjat yo'q (shubhali)
    df["no_docs"] = (df["docs_count"] == 0).astype("Int8")
    df["no_images"] = (df["images_count"] == 0).astype("Int8")

    # Yuqori zaklad foizi (>25 = normal, <10 = shubhali)
    df["low_zaklad"] = (
        df["zaklad_percent"].notna() & (df["zaklad_percent"] < 10)
    ).astype("Int8")

    # Kamayuvchi auksion (descending = shubhali pattern)
    df["is_descending_closed"] = (
        (df["is_descending"] == 1) & (df["is_closed"] == 1)
    ).astype("Int8")
    return df


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    df["start_hour"] = df["start_dt"].dt.hour
    df["start_weekday"] = df["start_dt"].dt.weekday
    df["start_month"] = df["start_dt"].dt.month
    df["is_weekend"] = df["start_weekday"].isin([5, 6]).astype("Int8")

    # Vaqt oralig'i (ariza muddati)
    df["duration_hours"] = (
        (df["end_dt"] - df["start_dt"]).dt.total_seconds() / 3600
    ).where(df["start_dt"].notna() & df["end_dt"].notna())

    df["is_short_duration"] = (df["duration_hours"] < 72).astype("Int8")
    df["is_very_short"] = (df["duration_hours"] < 24).astype("Int8")

    return df


def add_region_features(df: pd.DataFrame) -> pd.DataFrame:
    # Viloyat bo'yicha o'rtacha narx benchmark
    df["area_bin"] = pd.cut(
        df["start_price"],
        bins=[0, 5e6, 20e6, 100e6, 500e6, 1e12],
        labels=["xs", "s", "m", "l", "xl"],
    )
    grp = ["region_code", "property_group", "area_bin"]
    valid = df[grp + ["start_price"]].dropna(subset=["start_price", "region_code"])

    if len(valid) > 20:
        bm = (
            valid.groupby(grp, observed=True)["start_price"]
            .median()
            .reset_index()
            .rename(columns={"start_price": "benchmark_price"})
        )
        df = df.merge(bm, on=grp, how="left")
        std_v = df["start_price"].std()
        df["price_z_score"] = np.where(
            std_v > 0,
            (df["start_price"] - df["benchmark_price"]) / std_v,
            np.nan,
        )
        df["price_outlier"] = (df["price_z_score"].abs() > 2).astype("Int8")
    else:
        df["benchmark_price"] = np.nan
        df["price_z_score"] = np.nan
        df["price_outlier"] = pd.NA
    return df


def add_seller_features(df: pd.DataFrame) -> pd.DataFrame:
    grp = df.groupby("seller_user_id", dropna=False)
    stats = grp.agg(
        seller_total_lots=("lot_id", "count"),
        seller_avg_auction_cnt=("auction_cnt", "mean"),
        seller_no_docs_pct=("no_docs", "mean"),
        seller_closed_pct=("is_closed", "mean"),
    ).reset_index()
    df = df.merge(stats, on="seller_user_id", how="left")
    df["seller_is_heavy"] = (df["seller_total_lots"] >= 20).astype("Int8")
    return df


def add_red_flag_score(df: pd.DataFrame) -> pd.DataFrame:
    score = pd.Series(0.0, index=df.index)

    def sadd(col, w):
        s = df.get(col, pd.Series(dtype=float))
        return score + s.fillna(0).astype(float) * w

    score = sadd("is_closed", 2.5)
    score = sadd("is_single_step", 2.0)
    score = sadd("price_below_appraised", 2.0)
    score = sadd("is_short_duration", 1.0)
    score = sadd("is_very_short", 1.5)
    score = sadd("no_docs", 1.0)
    score = sadd("low_zaklad", 1.0)
    score = sadd("price_outlier", 1.5)
    score = sadd("is_descending_closed", 2.0)
    score = sadd("high_views_no_orders", 0.5)

    df["red_flag_score"] = score.clip(0, 10).round(2)
    df["is_high_risk"] = (df["red_flag_score"] >= 4).astype("Int8")
    return df


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    clean_path = os.path.join(DATA_DIR, "lots_clean.parquet")
    df = pd.read_parquet(clean_path)
    n = len(df)

    df = add_price_features(df)
    df = add_auction_features(df)
    df = add_time_features(df)
    df = add_region_features(df)
    df = add_seller_features(df)
    df = add_red_flag_score(df)

    feature_cols = [c for c in df.columns
                    if c not in ("images", "docs", "additional_info", "name",
                                 "address", "seller_name", "seller_phone",
                                 "seller_email", "lot_number")]
    out_path = os.path.join(DATA_DIR, "lots_features.parquet")
    df.to_parquet(out_path, index=False)

    with open(os.path.join(DATA_DIR, "features_stats.txt"), "w") as f:
        f.write(f"Rows: {n}\n")
        f.write(f"Cols: {len(df.columns)}\n")
        f.write(f"Feature cols: {len(feature_cols)}\n")
        f.write(f"is_high_risk=1: {int(df['is_high_risk'].sum())}\n")
        f.write(f"price_below_appraised=1: {int(df.get('price_below_appraised', pd.Series(0)).sum())}\n")
        f.write(f"is_single_step=1: {int(df['is_single_step'].sum())}\n")

    print(f"Saqlandi: {n} lot, {len(feature_cols)} feature -> {out_path}")
    print(f"is_high_risk=1: {int(df['is_high_risk'].sum())} ({df['is_high_risk'].mean()*100:.1f}%)")
    print(f"price_below_appraised: {int(df.get('price_below_appraised', pd.Series(0)).sum())}")
    print(f"is_single_step: {int(df['is_single_step'].sum())}")


if __name__ == "__main__":
    main()
