"""
Qadam 8: Topshirishdan oldin validatsiya checklist.

Ishlatish:
    python scripts/06_validate.py
"""

import os
import sys

import pandas as pd

DATA_DIR = "data"
PASS = "✓"
FAIL = "✗"
WARN = "!"

results = []


def check(name: str, passed: bool, detail: str = ""):
    symbol = PASS if passed else FAIL
    results.append((symbol, name, detail))
    print(f"  {symbol} {name}" + (f" — {detail}" if detail else ""))


def main():
    print("=" * 60)
    print("AuksionWatch Dataset Validatsiya")
    print("=" * 60)

    # ── lots_raw.parquet ─────────────────────────────────────────────────────
    print("\n[1] lots_raw.parquet")
    raw_path = os.path.join(DATA_DIR, "lots_raw.parquet")
    if os.path.exists(raw_path):
        df_raw = pd.read_parquet(raw_path)
        check("9000+ qator", len(df_raw) >= 9000, f"{len(df_raw):,} qator")
        check("lot_id unique", df_raw["lot_id"].is_unique, f"{df_raw['lot_id'].duplicated().sum()} duplikat")
    else:
        check("Fayl mavjud", False, raw_path)

    # ── lots_clean.parquet ───────────────────────────────────────────────────
    print("\n[2] lots_clean.parquet")
    clean_path = os.path.join(DATA_DIR, "lots_clean.parquet")
    if os.path.exists(clean_path):
        df_c = pd.read_parquet(clean_path)
        check("9000+ qator", len(df_c) >= 9000, f"{len(df_c):,} qator")

        for col in ["start_price", "start_time"]:
            if col in df_c.columns:
                null_pct = df_c[col].isna().mean() * 100
                check(f"{col} NaN < 5%", null_pct < 5, f"{null_pct:.1f}%")

        if "region_code" in df_c.columns:
            valid_codes = df_c["region_code"].str.startswith("UZ-").fillna(False)
            check("region_code UZ-XX format", valid_codes.mean() > 0.5,
                  f"{valid_codes.mean()*100:.1f}% to'g'ri")

        if "auction_type" in df_c.columns:
            valid_types = df_c["auction_type"].isin(["open", "closed", None])
            inv = (~df_c["auction_type"].isin(["open", "closed"]) & df_c["auction_type"].notna()).sum()
            check("auction_type faqat open/closed", inv == 0, f"{inv} noto'g'ri qiymat")
    else:
        check("Fayl mavjud", False, clean_path)

    # ── lots_features.parquet ────────────────────────────────────────────────
    print("\n[3] lots_features.parquet")
    feat_path = os.path.join(DATA_DIR, "lots_features.parquet")
    if os.path.exists(feat_path):
        df_f = pd.read_parquet(feat_path)
        feature_cols = [c for c in df_f.columns
                        if c not in ("raw_html", "description_emb", "images", "documents",
                                     "url", "scraped_at", "description", "raw_html",
                                     "lot_number", "seller_name", "address", "area_bin")]
        check("30+ feature", len(feature_cols) >= 30, f"{len(feature_cols)} feature")
        check("description_emb mavjud", "description_emb" in df_f.columns)
    else:
        check("Fayl mavjud", False, feat_path)

    # ── red_flags_labeled.csv ────────────────────────────────────────────────
    print("\n[4] red_flags_labeled.csv")
    label_path = os.path.join(DATA_DIR, "red_flags_labeled.csv")
    if os.path.exists(label_path):
        df_l = pd.read_csv(label_path)
        check("200 ta yorliq", len(df_l) >= 200, f"{len(df_l)} qator")
        check("is_suspicious ustuni", "is_suspicious" in df_l.columns)
        check("flag_type ustuni", "flag_type" in df_l.columns)
        if "is_suspicious" in df_l.columns:
            filled = df_l["is_suspicious"].notna().sum()
            check("Barcha to'ldirilgan", filled == len(df_l), f"{filled}/{len(df_l)} to'ldirilgan")
    else:
        check("Fayl mavjud", False, f"{label_path} — labeling tugaganmi?")

    # ── eda_report.html ──────────────────────────────────────────────────────
    print("\n[5] eda_report.html")
    eda_path = os.path.join(DATA_DIR, "eda_report.html")
    if os.path.exists(eda_path):
        size_kb = os.path.getsize(eda_path) / 1024
        check("Fayl mavjud", True, f"{size_kb:.0f} KB")
        check("Hajm > 100 KB", size_kb > 100, f"{size_kb:.0f} KB")
    else:
        check("Fayl mavjud", False, eda_path)

    # ── Skriptlar ────────────────────────────────────────────────────────────
    print("\n[6] Skriptlar")
    for script in ["scripts/00_get_lot_ids.py", "scripts/01_scrape_lots.py",
                    "scripts/02_clean.py", "scripts/03_features.py", "scripts/04_eda.py"]:
        check(script, os.path.exists(script))

    # ── Notebook ─────────────────────────────────────────────────────────────
    print("\n[7] Notebook")
    nb_path = os.path.join("notebooks", "notebook_eda.ipynb")
    check("notebook_eda.ipynb", os.path.exists(nb_path))

    # ── Natija ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    passed = sum(1 for r in results if r[0] == PASS)
    failed = sum(1 for r in results if r[0] == FAIL)
    print(f"Natija: {passed} ✓  |  {failed} ✗")
    if failed == 0:
        print("BARCHA TEKSHIRUVLAR O'TDI — topshirishga tayyor!")
    else:
        print(f"{failed} ta muammo bor — hal qilib qayta tekshiring.")
        sys.exit(1)


if __name__ == "__main__":
    main()
