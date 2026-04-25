"""
Qadam 4: API ma'lumotlarini tozalash.
Ishlatish: python scripts/02_clean.py
"""

import os
import re

import pandas as pd

DATA_DIR = "data"


def safe_float(v) -> float | None:
    try:
        return float(v) if v not in (None, "", "null") else None
    except (TypeError, ValueError):
        return None


def safe_int(v) -> int | None:
    f = safe_float(v)
    return int(f) if f is not None else None


def parse_datetime(s: str | None) -> pd.Timestamp | None:
    if not s:
        return None
    for fmt in ("%d.%m.%Y %H:%M", "%d.%m.%Y", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return pd.to_datetime(s.strip(), format=fmt)
        except (ValueError, AttributeError):
            pass
    return None


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    raw_path = os.path.join(DATA_DIR, "lots_raw.parquet")
    df = pd.read_parquet(raw_path)
    n0 = len(df)

    # ── Duplikat olib tashlash ────────────────────────────────────────────
    df = df.drop_duplicates("lot_id").reset_index(drop=True)

    # ── Numeric maydonlar ─────────────────────────────────────────────────
    for col in ["start_price", "current_price", "appraised_price", "min_price",
                "zaklad_summa", "step_summa"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["auction_cnt", "order_cnt", "view_count", "images_count", "docs_count",
                "lot_statuses_id", "regions_id", "exec_order_type_id", "seller_user_id"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    for col in ["zaklad_percent", "step_percent"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # ── Koordinatalar ─────────────────────────────────────────────────────
    df["geo_lat"] = pd.to_numeric(df["geo_lat"], errors="coerce")
    df["geo_lon"] = pd.to_numeric(df["geo_lon"], errors="coerce")

    # ── Sana maydonlari ───────────────────────────────────────────────────
    df["start_dt"] = df["start_time"].apply(parse_datetime)
    df["end_dt"] = df["order_end_time"].apply(parse_datetime)
    df["create_dt"] = df["create_time"].apply(parse_datetime)

    # ── Boolean'lar ───────────────────────────────────────────────────────
    for col in ["is_closed", "is_descending", "is_from_mib"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # ── sold_price: current > 0 bo'lsa current, aks holda start ──────────
    df["sold_price"] = df["current_price"].where(
        df["current_price"].notna() & (df["current_price"] > 0),
        df["start_price"]
    )

    # ── Seller INN: 9 raqam ───────────────────────────────────────────────
    df["seller_inn"] = df["seller_inn"].apply(
        lambda x: str(x).zfill(9) if pd.notna(x) and str(x).strip() else None
    )

    # ── auction_type tekshiruvi ───────────────────────────────────────────
    df["auction_type"] = df["is_closed"].map({0: "open", 1: "closed"})

    # ── Validatsiya ───────────────────────────────────────────────────────
    n1 = len(df)
    null_pct = (df.isna().mean() * 100).round(1)

    clean_path = os.path.join(DATA_DIR, "lots_clean.parquet")
    df.to_parquet(clean_path, index=False)

    with open(os.path.join(DATA_DIR, "clean_stats.txt"), "w") as f:
        f.write(f"Dastlabki: {n0}\n")
        f.write(f"Tozalangan: {n1}\n")
        f.write(f"Ustunlar: {len(df.columns)}\n\n")
        f.write("Null > 20%:\n")
        for col, pct in null_pct[null_pct > 20].items():
            f.write(f"  {col}: {pct}%\n")

    print(f"Saqlandi: {n1} lot -> {clean_path}")
    print(f"Ustunlar: {len(df.columns)}")
    print(f"start_dt notna: {df['start_dt'].notna().sum()}")
    print(f"geo_lat notna: {df['geo_lat'].notna().sum()}")


if __name__ == "__main__":
    main()
