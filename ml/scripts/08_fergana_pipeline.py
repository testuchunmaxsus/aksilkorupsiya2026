"""
Fergana.xlsx real dataset'dan ML pipeline.

Ishlatish: python scripts/08_fergana_pipeline.py
Natija:
    data/fergana_clean.parquet
    data/fergana_features.parquet
    data/fergana_predictions.csv   <-- asosiy chiqish
    data/fergana_report.txt        <-- insonlar uchun hisobot
"""

import os
import re
import sys
import warnings
import pickle

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import MinMaxScaler

warnings.filterwarnings("ignore")
DATA_DIR = "data"
MODEL_DIR = "models"

# ─── 1. YUKLASH ────────────────────────────────────────────────────────────────

def load_excel() -> pd.DataFrame:
    df = pd.read_excel(
        os.path.join(DATA_DIR, "Fergana.xlsx"),
        header=2,
    )
    df.columns = [
        "address", "building_area_m2", "appraised_price", "rental_area",
        "auction_date", "lot_number", "region", "district",
        "category", "serial_no", "start_price", "seller_name",
        "auction_settings", "property_type", "land_area_ga", "auction_count",
    ]
    df = df[df["lot_number"] != "Lot raqami"].reset_index(drop=True)
    return df


# ─── 2. TOZALASH ──────────────────────────────────────────────────────────────

def clean_price(s) -> float:
    """'1 416 780 000.0' → 1416780000.0"""
    if pd.isna(s):
        return np.nan
    return float(re.sub(r"[^\d.]", "", str(s))) if re.search(r"\d", str(s)) else np.nan


def clean_area(s) -> float:
    """'15490.71 m2' yoki '3392.81 m2' → 15490.71"""
    if pd.isna(s):
        return np.nan
    m = re.search(r"[\d.,]+", str(s).replace(",", "."))
    return float(m.group()) if m else np.nan


def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["start_price"]     = df["start_price"].apply(clean_price)
    df["appraised_price"] = df["appraised_price"].apply(clean_price)
    df["building_area_m2"] = df["building_area_m2"].apply(clean_area)
    df["land_area_ga"]    = df["land_area_ga"].apply(clean_area)
    df["auction_count"]   = pd.to_numeric(df["auction_count"], errors="coerce").astype("Int64")
    df["lot_number"]      = pd.to_numeric(df["lot_number"], errors="coerce").astype("Int64")
    df["auction_date"]    = pd.to_datetime(df["auction_date"], errors="coerce")
    df["serial_no"]       = pd.to_numeric(df["serial_no"], errors="coerce").astype("Int64")

    df["lot_url"] = "https://e-auksion.uz/lot-view?lot_id=" + df["lot_number"].astype(str)

    df = df.drop_duplicates("lot_number").reset_index(drop=True)
    return df


# ─── 3. FEATURE ENGINEERING ──────────────────────────────────────────────────

CATEGORY_RISK = {
    "Bankrotlik": 3.0,
    "Koʻchma savdo obyektlari": 2.0,
    "Noturar-joy obyektlari": 2.0,
    "Boshqa turdagi mulklar": 1.5,
    "Davlat obyekti": 1.5,
    "Tadbirkorlik va shaharsozlik uchun": 1.0,
    "Dehqon xo'jaligi yuritish uchun yer uchastkalarini ijaraga berish": 0.5,
    "Yoshlarga dehqon xo'jaligini yuritish uchun yer uchastkalari": 0.5,
}

SETTINGS_RISK = {
    "Bankrotlik": 3.0,
    "Odatiy sozlama": 1.5,
    "Hamma uchun sozlama (Shartnomalik)": 1.0,
    "Hamma uchun sozlama": 0.8,
    "K-SAVDO obyektlari": 1.5,
}


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # ── Narx featurelari ─────────────────────────────────────────────────
    df["price_ratio"] = np.where(
        (df["appraised_price"] > 0) & df["appraised_price"].notna(),
        df["start_price"] / df["appraised_price"],
        np.nan,
    )
    # start_price == appraised_price: chegirma yo'q
    df["no_discount"] = (
        (df["price_ratio"] >= 0.999) & df["price_ratio"].notna()
    ).astype(int)

    df["price_below_70pct"] = (
        (df["price_ratio"] < 0.70) & df["price_ratio"].notna()
    ).astype(int)

    # Juda kuchli signal: narx baholashning 10% dan past
    df["price_below_10pct"] = (
        (df["price_ratio"] < 0.10) & df["price_ratio"].notna()
    ).astype(int)

    df["price_above_130pct"] = (
        (df["price_ratio"] > 1.30) & df["price_ratio"].notna()
    ).astype(int)

    df["start_price_log"]     = np.log1p(df["start_price"].fillna(0))
    df["appraised_price_log"] = np.log1p(df["appraised_price"].fillna(0))
    df["price_diff"]          = df["start_price"] - df["appraised_price"]
    df["price_diff_log"]      = np.sign(df["price_diff"]) * np.log1p(df["price_diff"].abs())

    # ── Auksion qayta-qayta e'lon signallari ──────────────────────────────
    df["auction_count"]     = df["auction_count"].fillna(1)
    df["auction_count_log"] = np.log1p(df["auction_count"])

    df["is_repeated"]       = (df["auction_count"] > 3).astype(int)
    df["is_very_repeated"]  = (df["auction_count"] > 20).astype(int)
    df["is_mega_repeated"]  = (df["auction_count"] > 50).astype(int)
    df["is_ultra_repeated"] = (df["auction_count"] > 100).astype(int)

    # ── Vaqt featurelari ─────────────────────────────────────────────────
    df["auction_month"]   = df["auction_date"].dt.month
    df["auction_weekday"] = df["auction_date"].dt.weekday
    df["is_weekend"]      = df["auction_weekday"].isin([5, 6]).astype(int)
    df["auction_hour"]    = df["auction_date"].dt.hour

    # ── Kategoriya va sozlama risk ────────────────────────────────────────
    df["category_risk"] = df["auction_settings"].map(SETTINGS_RISK).fillna(
        df["category"].map(CATEGORY_RISK).fillna(1.0)
    )
    df["is_bankruptcy"]  = df["auction_settings"].str.contains("Bankrot", na=False).astype(int)
    df["is_k_savdo"]     = df["auction_settings"].str.contains("K-SAVDO", na=False).astype(int)
    df["is_rental"]      = df["auction_settings"].str.contains("[Ii]jara", na=False).astype(int)

    # Bankrotlik + chegirma yo'q = maxsus qo'shma signal (juda shubhali)
    df["bankruptcy_no_discount"] = (
        (df["is_bankruptcy"] == 1) & (df["no_discount"] == 1)
    ).astype(int)

    # ── Mulk turi risk ────────────────────────────────────────────────────
    df["is_land"]        = df["property_type"].str.contains("[Yy]er", na=False).astype(int)
    df["is_real_estate"] = df["property_type"].str.contains("[Kk]o.chmas", na=False).astype(int)
    df["is_vehicle"]     = df["property_type"].str.contains("[Aa]vtotransport", na=False).astype(int)
    df["is_state_asset"] = df["property_type"].str.contains("Davlat", na=False).astype(int)

    # ── Sotuvchi featurelari ──────────────────────────────────────────────
    seller_counts = df.groupby("seller_name")["lot_number"].count().rename("seller_lot_count")
    df = df.merge(seller_counts, on="seller_name", how="left")
    df["seller_lot_count"] = df["seller_lot_count"].fillna(1)
    df["seller_is_heavy"]  = (df["seller_lot_count"] >= 10).astype(int)

    # Bir tumanda mediana narx benchmark
    district_median = df.groupby(["district", "property_type"])["start_price"].median()
    def get_median(row):
        return district_median.get((row["district"], row["property_type"]), np.nan)
    df["district_median_price"] = df.apply(get_median, axis=1)
    df["price_vs_district"] = df["start_price"] / df["district_median_price"].replace(0, np.nan)

    # ── Maydon featurelari ────────────────────────────────────────────────
    df["has_building_area"] = df["building_area_m2"].notna().astype(int)
    df["has_land_area"]     = df["land_area_ga"].notna().astype(int)
    df["building_area_log"] = np.log1p(df["building_area_m2"].fillna(0))
    df["land_area_log"]     = np.log1p(df["land_area_ga"].fillna(0))

    df["price_per_m2"] = np.where(
        (df["building_area_m2"] > 0) & df["building_area_m2"].notna(),
        df["start_price"] / df["building_area_m2"],
        np.nan,
    )
    df["price_per_ga"] = np.where(
        (df["land_area_ga"] > 0) & df["land_area_ga"].notna(),
        df["start_price"] / df["land_area_ga"],
        np.nan,
    )

    # ── District encoding ─────────────────────────────────────────────────
    dist_map = {d: i for i, d in enumerate(df["district"].dropna().unique())}
    df["district_id"] = df["district"].map(dist_map).fillna(-1).astype(int)

    return df


# ─── 4. ML SCORING ────────────────────────────────────────────────────────────

ML_FEATURES = [
    "start_price_log", "appraised_price_log", "price_ratio", "price_diff_log",
    "price_below_70pct", "price_below_10pct", "no_discount", "price_above_130pct",
    "auction_count", "auction_count_log",
    "is_repeated", "is_very_repeated", "is_mega_repeated", "is_ultra_repeated",
    "category_risk", "is_bankruptcy", "is_k_savdo", "is_rental",
    "bankruptcy_no_discount",
    "is_land", "is_real_estate", "is_vehicle", "is_state_asset",
    "seller_lot_count", "seller_is_heavy",
    "building_area_log", "land_area_log", "has_building_area", "has_land_area",
    "auction_month", "auction_weekday", "is_weekend",
    "district_id",
]


def rule_score(df: pd.DataFrame) -> pd.Series:
    """Qoidalarga asoslangan red flag score (0–10)."""
    score = pd.Series(0.0, index=df.index)

    # ── Narx anomaliyalari ────────────────────────────────────────────────
    score += df["price_below_70pct"].fillna(0) * 2.0
    score += df["price_below_10pct"].fillna(0) * 3.0   # qo'shimcha +3 juda past narx uchun
    score += df["no_discount"].fillna(0) * 1.5

    # ── Bankrotlik signallari ─────────────────────────────────────────────
    score += df["is_bankruptcy"].fillna(0) * 2.0
    # Bankrotlik + chegirma yo'q = alohida kuchli signal
    score += df["bankruptcy_no_discount"].fillna(0) * 3.0

    # ── Qayta-qayta e'lon ─────────────────────────────────────────────────
    score += df["is_repeated"].fillna(0) * 0.5
    score += df["is_very_repeated"].fillna(0) * 1.0
    score += df["is_mega_repeated"].fillna(0) * 1.5
    score += df["is_ultra_repeated"].fillna(0) * 2.0

    # ── K-SAVDO va boshqa toifalar ────────────────────────────────────────
    score += df["is_k_savdo"].fillna(0) * 1.0
    score += (df["category_risk"] - 1.0).clip(0) * 0.5

    # ── Davlat aktivlari past narxda ──────────────────────────────────────
    score += (df["is_state_asset"] * df["price_below_70pct"]).fillna(0) * 1.0

    return score.clip(0, 10).round(2)


def isolation_score(df: pd.DataFrame) -> pd.Series:
    feats = [f for f in ML_FEATURES if f in df.columns]
    X = df[feats].copy()
    for col in X.columns:
        X[col] = pd.to_numeric(X[col], errors="coerce").fillna(
            X[col].median() if X[col].notna().any() else 0
        )

    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    clf = IsolationForest(
        n_estimators=200, contamination=0.12,
        max_samples="auto", random_state=42, n_jobs=-1,
    )
    clf.fit(X_scaled)
    scores = -clf.score_samples(X_scaled)
    return pd.Series(scores, index=df.index, name="iso_score")


# ─── 5. WHY FLAGGED ──────────────────────────────────────────────────────────

def build_reason(row) -> str:
    """Lot nima uchun shubhali ekanini izohlaydi."""
    parts = []

    ratio = row.get("price_ratio", np.nan)
    if pd.notna(ratio):
        pct = int(round(ratio * 100))
        if ratio < 0.10:
            parts.append(f"Narx baholashning atigi {pct}% ({row['start_price']:,.0f} vs {row['appraised_price']:,.0f})")
        elif ratio < 0.70:
            parts.append(f"Narx baholashdan {100-pct}% past ({row['start_price']:,.0f} vs {row['appraised_price']:,.0f})")
        elif ratio >= 0.999:
            parts.append("Chegirmasiz (boshlanish narxi = baholash narxi)")

    cnt = int(row.get("auction_count", 0))
    if cnt > 100:
        parts.append(f"{cnt} marta qayta e'lon (juda uzoq sotilmagan)")
    elif cnt > 50:
        parts.append(f"{cnt} marta qayta e'lon")
    elif cnt > 20:
        parts.append(f"{cnt} marta qayta e'lon")

    if row.get("is_bankruptcy", 0):
        if row.get("no_discount", 0):
            parts.append("BANKROTLIK + chegirma yo'q (juda shubhali!)")
        else:
            parts.append("Bankrotlik sababli sotilmoqda")

    if row.get("is_k_savdo", 0):
        parts.append("K-SAVDO (ko'chma savdo joyi)")

    if row.get("seller_is_heavy", 0):
        parts.append(f"Bir sotuvchi {int(row.get('seller_lot_count',0))} ta lot chiqargan")

    return " | ".join(parts) if parts else "Statistik anomaliya"


# ─── 6. DYNAMIC THRESHOLDS ──────────────────────────────────────────────────

def assign_risk_level(scores: pd.Series) -> pd.Categorical:
    """
    Kvantilelarga asoslangan dinamik chegaralar.
    KRITIK: eng yuqori 2%, YUQORI: 2-10%, O'RTA: 10-40%, PAST: qolgan.
    """
    p98 = scores.quantile(0.98)
    p90 = scores.quantile(0.90)
    p60 = scores.quantile(0.60)

    def classify(s):
        if s >= p98:
            return "KRITIK"
        elif s >= p90:
            return "YUQORI"
        elif s >= p60:
            return "O'RTA"
        else:
            return "PAST"

    return scores.apply(classify)


# ─── 7. MAIN ──────────────────────────────────────────────────────────────────

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(MODEL_DIR, exist_ok=True)

    sys.stderr.write("1. Yuklanmoqda...\n")
    df = load_excel()
    sys.stderr.write(f"   {len(df)} lot yuklandi\n")

    sys.stderr.write("2. Tozalanmoqda...\n")
    df = clean_df(df)
    df.to_parquet(os.path.join(DATA_DIR, "fergana_clean.parquet"), index=False)

    sys.stderr.write("3. Featurelar hisoblanmoqda...\n")
    df = add_features(df)
    df.to_parquet(os.path.join(DATA_DIR, "fergana_features.parquet"), index=False)

    sys.stderr.write("4. ML scoring...\n")
    df["rule_score"] = rule_score(df)
    df["iso_score"]  = isolation_score(df)

    mms = MinMaxScaler()
    df["iso_norm"]   = mms.fit_transform(df[["iso_score"]]).flatten()
    df["rule_norm"]  = df["rule_score"] / 10.0
    df["risk_score"] = (df["rule_norm"] * 0.55 + df["iso_norm"] * 0.45).round(4)

    # Dinamik kvantilelarga asoslangan darajalar
    df["risk_level"] = assign_risk_level(df["risk_score"])

    # Nima uchun shubhali izohi
    sys.stderr.write("5. Izohlar yozilyapti...\n")
    df["why_flagged"] = df.apply(build_reason, axis=1)

    # ── Chiqish fayli ─────────────────────────────────────────────────────
    output_cols = [
        "lot_number", "lot_url", "address", "district", "category",
        "property_type", "auction_settings", "seller_name",
        "start_price", "appraised_price", "price_ratio",
        "auction_count", "auction_date",
        "rule_score", "iso_score", "risk_score", "risk_level",
        "why_flagged",
        "price_below_10pct", "price_below_70pct", "no_discount",
        "is_bankruptcy", "bankruptcy_no_discount",
        "is_repeated", "is_very_repeated", "is_mega_repeated", "is_ultra_repeated",
        "is_k_savdo", "seller_lot_count",
    ]
    avail   = [c for c in output_cols if c in df.columns]
    df_out  = df[avail].sort_values("risk_score", ascending=False)
    df_out.to_csv(
        os.path.join(DATA_DIR, "fergana_predictions.csv"),
        index=False, encoding="utf-8-sig",
    )

    # ── Hisobot ───────────────────────────────────────────────────────────
    lvl   = df["risk_level"].value_counts()
    score_p50  = df["risk_score"].quantile(0.50)
    score_p90  = df["risk_score"].quantile(0.90)
    score_p98  = df["risk_score"].quantile(0.98)
    score_max  = df["risk_score"].max()

    top20 = df.nlargest(20, "risk_score")[
        ["lot_number", "district", "start_price", "appraised_price",
         "price_ratio", "auction_count", "risk_score", "why_flagged"]
    ]

    bankrupt_no_disc = int(df["bankruptcy_no_discount"].sum())
    extreme_low      = int(df["price_below_10pct"].sum())

    report_lines = [
        "=" * 70,
        "FERGANA VILOYATI — RED FLAG HISOBOT (Kvantilelarga asoslangan)",
        f"Sana: {pd.Timestamp.now().strftime('%d.%m.%Y %H:%M')}",
        "=" * 70,
        f"\nJami lot: {len(df):,}",
        "",
        "RISK DARAJASI BO'YICHA (dinamik kvantil chegaralar):",
        f"  KRITIK  (eng yuqori 2%):  {lvl.get('KRITIK',  0):>6,} lot  (threshold >= {score_p98:.3f})",
        f"  YUQORI  (2% - 10%):       {lvl.get('YUQORI',  0):>6,} lot  (threshold >= {score_p90:.3f})",
        "  O'RTA   (10% - 40%):     {:>6,} lot".format(lvl.get("O'RTA", 0)),
        f"  PAST    (qolgan 60%):     {lvl.get('PAST',    0):>6,} lot",
        "",
        "SCORE TAQSIMOTI:",
        f"  Median (p50):  {score_p50:.3f}",
        f"  p90:           {score_p90:.3f}",
        f"  p98 (KRITIK):  {score_p98:.3f}",
        f"  Maksimal:      {score_max:.3f}",
        "",
        "ASOSIY SIGNAL STATISTIKASI:",
        f"  Narx baholashdan 10% PAST (juda kuchli):  {extreme_low:>6,}",
        f"  Narx baholashdan 70% past:                {int(df['price_below_70pct'].sum()):>6,}",
        f"  Chegirmasiz (start==appraised):           {int(df['no_discount'].sum()):>6,}",
        f"  Bankrotlik lotlari:                       {int(df['is_bankruptcy'].sum()):>6,}",
        f"  Bankrotlik + chegirmasiz (alohida xavf):  {bankrupt_no_disc:>6,}",
        f"  3+ marta qayta e'lon:                     {int(df['is_repeated'].sum()):>6,}",
        f"  20+ marta qayta e'lon:                    {int(df['is_very_repeated'].sum()):>6,}",
        f"  50+ marta qayta e'lon:                    {int(df['is_mega_repeated'].sum()):>6,}",
        f"  100+ marta qayta e'lon:                   {int(df['is_ultra_repeated'].sum()):>6,}",
        f"  K-SAVDO lotlari:                          {int(df['is_k_savdo'].sum()):>6,}",
        "",
        "KATEGORIYA BO'YICHA KRITIK LOTLAR:",
    ]

    cat_kritik = df[df["risk_level"] == "KRITIK"]["category"].value_counts().head(10)
    if cat_kritik.empty:
        report_lines.append("  (KRITIK lot topilmadi)")
    else:
        for cat, cnt in cat_kritik.items():
            report_lines.append(f"  {cnt:>5} | {str(cat)[:60]}")

    report_lines += ["", "TUMAN BO'YICHA KRITIK LOTLAR:"]
    dist_kritik = df[df["risk_level"] == "KRITIK"]["district"].value_counts().head(10)
    if dist_kritik.empty:
        report_lines.append("  (KRITIK lot topilmadi)")
    else:
        for dist, cnt in dist_kritik.items():
            report_lines.append(f"  {cnt:>5} | {str(dist)}")

    report_lines += [
        "",
        "TOP 20 ENG SHUBHALI LOT:",
        f"{'Lot':<12} {'Tuman':<22} {'Narx':>14} {'Bahola':>14} {'%':>5} {'N':>5}  {'Score'}  Sabab",
        "-" * 110,
    ]
    for _, row in top20.iterrows():
        ratio_pct = f"{row.get('price_ratio', 0)*100:.0f}%" if pd.notna(row.get("price_ratio")) else "N/A"
        reason_short = str(row.get("why_flagged", ""))[:45]
        report_lines.append(
            f"{str(row.get('lot_number','')):<12} "
            f"{str(row.get('district',''))[:20]:<22} "
            f"{row.get('start_price', 0):>14,.0f} "
            f"{row.get('appraised_price', 0):>14,.0f} "
            f"{ratio_pct:>5} "
            f"{int(row.get('auction_count', 0)):>5}  "
            f"{row.get('risk_score', 0):.3f}  "
            f"{reason_short}"
        )

    report_lines += [
        "",
        "=" * 70,
        "BANKROTLIK + CHEGIRMASIZ (juda shubhali kombinatsiya):",
        f"{'Lot':<12} {'Tuman':<22} {'Narx':>14} {'Bahola':>14}  Score",
        "-" * 75,
    ]
    bankrupt_df = df[(df["is_bankruptcy"] == 1) & (df["no_discount"] == 1)].nlargest(10, "risk_score")
    for _, row in bankrupt_df.iterrows():
        report_lines.append(
            f"{str(row.get('lot_number','')):<12} "
            f"{str(row.get('district',''))[:20]:<22} "
            f"{row.get('start_price',0):>14,.0f} "
            f"{row.get('appraised_price',0):>14,.0f}  "
            f"{row.get('risk_score',0):.3f}"
        )

    report = "\n".join(report_lines)
    with open(os.path.join(DATA_DIR, "fergana_report.txt"), "w", encoding="utf-8") as f:
        f.write(report)

    # ── Statistika ────────────────────────────────────────────────────────
    sys.stderr.write("\nSaqlandi:\n")
    sys.stderr.write("  data/fergana_clean.parquet\n")
    sys.stderr.write("  data/fergana_features.parquet\n")
    sys.stderr.write("  data/fergana_predictions.csv\n")
    sys.stderr.write("  data/fergana_report.txt\n")
    sys.stderr.write("\n--- NATIJA ---\n")
    sys.stderr.write(f"KRITIK: {lvl.get('KRITIK', 0)} | YUQORI: {lvl.get('YUQORI', 0)}\n")
    sys.stderr.write(f"Score p50={score_p50:.3f} p90={score_p90:.3f} p98={score_p98:.3f} max={score_max:.3f}\n")
    sys.stderr.write(f"Bankrotlik+chegirmasiz: {bankrupt_no_disc}\n")
    sys.stderr.write(f"Juda past narx (<10%): {extreme_low}\n")


if __name__ == "__main__":
    main()
