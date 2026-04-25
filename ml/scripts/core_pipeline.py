"""
Universal AuksionWatch pipeline.
CSV yoki Excel (har qanday viloyat) → predictions + report.

Ishlatish:
    from scripts.core_pipeline import run_pipeline
    result = run_pipeline("data/Fergana.xlsx")
    result = run_pipeline("data/input.csv")
"""

import io
import re
import sys
import warnings
import os
from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import MinMaxScaler, StandardScaler

warnings.filterwarnings("ignore")

# ─── COLUMN DETECTION ────────────────────────────────────────────────────────
# e-auksion.uz export ustunlarini standart nomga map qilish
COLUMN_ALIASES = {
    "address": [
        "manzili", "manzil", "address", "адрес",
    ],
    "building_area_m2": [
        "бино майдони", "bino maydoni", "building_area", "area_m2",
        "bino maydoni kv.m.", "бино майдони кв.м.",
    ],
    "appraised_price": [
        "baholangan narx", "baholash narxi", "appraised_price",
        "baholangan", "баҳоланган нарх",
    ],
    "rental_area": [
        "ijara maydoni", "rental_area", "ижара майдони",
    ],
    "auction_date": [
        "oxirgi auksion sanasi", "auksion sanasi", "auction_date",
        "oxirgi auksion", "сана",
    ],
    "lot_number": [
        "lot raqami", "lot_number", "lot_id", "лот рақами",
        "lot", "raqam",
    ],
    "region": [
        "вилоят", "viloyat", "region", "viloyati",
    ],
    "district": [
        "туман/шаҳар", "tuman", "shahar", "district",
        "туман", "шаҳар", "tuman/shahar",
    ],
    "category": [
        "категория номи", "kategoriya nomi", "category",
        "категория", "kategoriya",
    ],
    "serial_no": [
        "t/r", "tartib raqami", "serial_no", "no", "n",
        "т/р", "#",
    ],
    "start_price": [
        "boshlang'ich narx", "boshlanish narxi", "start_price",
        "boshlangich narx", "boshlang`ich narx",
        "бошланғич нарх",
    ],
    "seller_name": [
        "буюртмачи номи", "buyurtmachi nomi", "seller_name",
        "sotuvchi", "buyurtmachi",
    ],
    "auction_settings": [
        "созламалар", "sozlamalar", "auction_settings",
        "settings", "sozlama", "аuksion sozlamalari",
    ],
    "property_type": [
        "мулк тури", "mulk turi", "property_type",
        "tur", "mulk",
    ],
    "land_area_ga": [
        "ер майдони (га)", "yer maydoni", "land_area",
        "yer maydoni (ga)", "ер майдони", "land_area_ga",
        "ga", "gektar",
    ],
    "auction_count": [
        "necha marta savdoga chiqarilganligi", "auction_count",
        "savdo soni", "marta", "necha marta",
    ],
}


def _normalize_col(s: str) -> str:
    return str(s).lower().strip().replace("\xa0", " ")


def detect_and_rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Har qanday ustun nomini standart nomga o'tkazadi."""
    rename_map = {}
    for std_name, aliases in COLUMN_ALIASES.items():
        for col in df.columns:
            normed = _normalize_col(col)
            if any(normed == _normalize_col(a) or normed.startswith(_normalize_col(a)) for a in aliases):
                if std_name not in rename_map.values():
                    rename_map[col] = std_name
                    break
    return df.rename(columns=rename_map)


# ─── LOADERS ─────────────────────────────────────────────────────────────────

def load_file(path: Union[str, Path, io.BytesIO], filename: str = "") -> pd.DataFrame:
    """
    CSV yoki Excel faylni yuklaydi.
    Excel: avtomat header row topadi (e-auksion.uz format: row 2 yoki 3).
    """
    ext = Path(filename or str(path)).suffix.lower() if not isinstance(path, io.BytesIO) else ""
    if not ext:
        ext = Path(str(path)).suffix.lower() if not isinstance(path, io.BytesIO) else ".xlsx"

    if ext in (".xlsx", ".xls"):
        # Header qatorini topish (lot_number yoki lot raqami mavjud qatorni)
        for header_row in [0, 1, 2, 3]:
            try:
                df = pd.read_excel(path, header=header_row)
                df_renamed = detect_and_rename_columns(df)
                if "lot_number" in df_renamed.columns:
                    df_renamed = df_renamed[df_renamed["lot_number"].notna()]
                    # Header qatorining o'zini olib tashlash
                    mask = df_renamed["lot_number"].astype(str).str.lower().str.contains(
                        "lot|raqam|№", na=False
                    )
                    df_renamed = df_renamed[~mask].reset_index(drop=True)
                    return df_renamed
            except Exception:
                continue
        # Fallback: header=2 (fergana format)
        df = pd.read_excel(path, header=2)
        df.columns = [
            "address", "building_area_m2", "appraised_price", "rental_area",
            "auction_date", "lot_number", "region", "district", "category",
            "serial_no", "start_price", "seller_name", "auction_settings",
            "property_type", "land_area_ga", "auction_count",
        ]
        df = df[df["lot_number"] != "Lot raqami"].reset_index(drop=True)
        return df
    else:
        # CSV — encoding'ni avtomat topadi
        for enc in ("utf-8-sig", "utf-8", "cp1251", "latin-1"):
            try:
                df = pd.read_csv(path, encoding=enc)
                return detect_and_rename_columns(df)
            except Exception:
                continue
        raise ValueError("CSV o'qilmadi. Encoding tekshiring.")


# ─── CLEANING ────────────────────────────────────────────────────────────────

def _clean_price(s) -> float:
    if pd.isna(s):
        return np.nan
    return float(re.sub(r"[^\d.]", "", str(s))) if re.search(r"\d", str(s)) else np.nan


def _clean_area(s) -> float:
    if pd.isna(s):
        return np.nan
    m = re.search(r"[\d.,]+", str(s).replace(",", "."))
    return float(m.group()) if m else np.nan


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col in ("start_price", "appraised_price"):
        if col in df.columns:
            df[col] = df[col].apply(_clean_price)

    for col in ("building_area_m2", "land_area_ga"):
        if col in df.columns:
            df[col] = df[col].apply(_clean_area)

    if "auction_count" in df.columns:
        df["auction_count"] = pd.to_numeric(df["auction_count"], errors="coerce").fillna(1)

    if "lot_number" in df.columns:
        df["lot_number"] = pd.to_numeric(df["lot_number"], errors="coerce")

    if "auction_date" in df.columns:
        df["auction_date"] = pd.to_datetime(df["auction_date"], errors="coerce")

    # lot_url
    if "lot_number" in df.columns:
        df["lot_url"] = "https://e-auksion.uz/lot-view?lot_id=" + df["lot_number"].astype(str)

    # Duplikat olib tashlash
    if "lot_number" in df.columns:
        df = df.drop_duplicates("lot_number").reset_index(drop=True)

    # Majburiy ustunlar bo'lmasa bo'sh qiymat
    for col in ("seller_name", "district", "category", "auction_settings", "property_type"):
        if col not in df.columns:
            df[col] = ""

    df["district"]          = df["district"].fillna("Noma'lum")
    df["category"]          = df["category"].fillna("Boshqa")
    df["auction_settings"]  = df["auction_settings"].fillna("")
    df["seller_name"]       = df["seller_name"].fillna("Noma'lum")

    return df


# ─── FEATURE ENGINEERING ─────────────────────────────────────────────────────

SETTINGS_RISK = {
    "Bankrotlik": 3.0,
    "Odatiy sozlama": 1.5,
    "Hamma uchun sozlama (Shartnomalik)": 1.0,
    "Hamma uchun sozlama": 0.8,
    "K-SAVDO obyektlari": 1.5,
}

CATEGORY_RISK = {
    "Bankrotlik": 3.0,
    "Koʻchma savdo obyektlari": 2.0,
    "Noturar-joy obyektlari": 2.0,
    "Boshqa turdagi mulklar": 1.5,
    "Davlat obyekti": 1.5,
    "Tadbirkorlik va shaharsozlik uchun": 1.0,
}


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Narx
    ap = df.get("appraised_price", pd.Series(np.nan, index=df.index))
    sp = df.get("start_price", pd.Series(np.nan, index=df.index))
    df["price_ratio"] = np.where((ap > 0) & ap.notna(), sp / ap, np.nan)
    df["no_discount"]        = ((df["price_ratio"] >= 0.999) & df["price_ratio"].notna()).astype(int)
    df["price_below_70pct"]  = ((df["price_ratio"] < 0.70)  & df["price_ratio"].notna()).astype(int)
    df["price_below_10pct"]  = ((df["price_ratio"] < 0.10)  & df["price_ratio"].notna()).astype(int)
    df["price_above_130pct"] = ((df["price_ratio"] > 1.30)  & df["price_ratio"].notna()).astype(int)
    df["start_price_log"]    = np.log1p(sp.fillna(0))
    df["appraised_price_log"]= np.log1p(ap.fillna(0))
    df["price_diff_log"]     = np.sign(sp - ap) * np.log1p((sp - ap).abs())

    # Auksion davomiyligi
    ac = df["auction_count"].fillna(1)
    df["auction_count"]      = ac
    df["auction_count_log"]  = np.log1p(ac)
    df["is_repeated"]        = (ac > 3).astype(int)
    df["is_very_repeated"]   = (ac > 20).astype(int)
    df["is_mega_repeated"]   = (ac > 50).astype(int)
    df["is_ultra_repeated"]  = (ac > 100).astype(int)

    # Vaqt
    if "auction_date" in df.columns and df["auction_date"].notna().any():
        df["auction_month"]   = df["auction_date"].dt.month.fillna(0).astype(int)
        df["auction_weekday"] = df["auction_date"].dt.weekday.fillna(0).astype(int)
        df["is_weekend"]      = df["auction_weekday"].isin([5, 6]).astype(int)
    else:
        df["auction_month"]   = 0
        df["auction_weekday"] = 0
        df["is_weekend"]      = 0

    # Kategoriya risk
    s = df["auction_settings"].fillna("")
    c = df["category"].fillna("")
    df["category_risk"]    = s.map(SETTINGS_RISK).fillna(c.map(CATEGORY_RISK).fillna(1.0))
    df["is_bankruptcy"]    = s.str.contains("Bankrot", na=False).astype(int)
    df["is_k_savdo"]       = s.str.contains("K-SAVDO", na=False).astype(int)
    df["is_rental"]        = s.str.contains("[Ii]jara", na=False).astype(int)
    df["bankruptcy_no_discount"] = ((df["is_bankruptcy"] == 1) & (df["no_discount"] == 1)).astype(int)

    # Mulk turi
    pt = df.get("property_type", pd.Series("", index=df.index)).fillna("")
    df["is_land"]        = pt.str.contains("[Yy]er", na=False).astype(int)
    df["is_real_estate"] = pt.str.contains("[Kk]o.chmas", na=False).astype(int)
    df["is_vehicle"]     = pt.str.contains("[Aa]vtotransport", na=False).astype(int)
    df["is_state_asset"] = pt.str.contains("Davlat", na=False).astype(int)

    # Sotuvchi
    seller_counts = df.groupby("seller_name")["seller_name"].transform("count")
    df["seller_lot_count"] = seller_counts.fillna(1)
    df["seller_is_heavy"]  = (df["seller_lot_count"] >= 10).astype(int)

    # Tuman benchmark
    try:
        dist_median = df.groupby(["district", "property_type"])["start_price"].transform("median")
        df["district_median_price"] = dist_median
        df["price_vs_district"] = sp / dist_median.replace(0, np.nan)
    except Exception:
        df["price_vs_district"] = np.nan

    # Maydon
    ba = df.get("building_area_m2", pd.Series(np.nan, index=df.index)).fillna(0)
    la = df.get("land_area_ga", pd.Series(np.nan, index=df.index)).fillna(0)
    df["building_area_log"] = np.log1p(ba)
    df["land_area_log"]     = np.log1p(la)
    df["has_building_area"] = (df.get("building_area_m2", pd.Series(np.nan, index=df.index)).notna()).astype(int)
    df["has_land_area"]     = (df.get("land_area_ga", pd.Series(np.nan, index=df.index)).notna()).astype(int)

    # District encoding
    dist_map = {d: i for i, d in enumerate(df["district"].dropna().unique())}
    df["district_id"] = df["district"].map(dist_map).fillna(-1).astype(int)

    return df


# ─── SCORING ─────────────────────────────────────────────────────────────────

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
    s = pd.Series(0.0, index=df.index)
    s += df.get("price_below_10pct", 0) * 3.0
    s += df.get("price_below_70pct", 0) * 2.0
    s += df.get("no_discount", 0) * 1.5
    s += df.get("is_bankruptcy", 0) * 2.0
    s += df.get("bankruptcy_no_discount", 0) * 3.0
    s += df.get("is_repeated", 0) * 0.5
    s += df.get("is_very_repeated", 0) * 1.0
    s += df.get("is_mega_repeated", 0) * 1.5
    s += df.get("is_ultra_repeated", 0) * 2.0
    s += df.get("is_k_savdo", 0) * 1.0
    s += (df.get("category_risk", 1.0) - 1.0).clip(0) * 0.5
    s += (df.get("is_state_asset", 0) * df.get("price_below_70pct", 0)) * 1.0
    return s.fillna(0).clip(0, 10).round(2)


def _prepare_X(df: pd.DataFrame, feats: list, scaler=None):
    X = df[feats].copy()
    for col in X.columns:
        X[col] = pd.to_numeric(X[col], errors="coerce")
        X[col] = X[col].fillna(X[col].median() if X[col].notna().any() else 0)
    if scaler is not None:
        return scaler.transform(X)
    return StandardScaler().fit_transform(X)


def _load_model(path: str):
    import pickle
    if not os.path.exists(path):
        return None
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except Exception:
        return None


def iso_score(df: pd.DataFrame) -> pd.Series:
    bundle = _load_model(os.path.join("models", "isolation_forest.pkl"))
    feats  = [f for f in ML_FEATURES if f in df.columns]
    if bundle and isinstance(bundle, dict) and "model" in bundle:
        saved_feats  = [f for f in bundle.get("features", feats) if f in df.columns]
        X_scaled     = _prepare_X(df, saved_feats, bundle.get("scaler"))
        return pd.Series(-bundle["model"].score_samples(X_scaled), index=df.index)
    # Fallback: fresh train
    X_scaled = _prepare_X(df, feats)
    clf = IsolationForest(n_estimators=200, contamination=0.12, random_state=42, n_jobs=-1)
    return pd.Series(-clf.fit(X_scaled).score_samples(X_scaled), index=df.index)


def xgb_score(df: pd.DataFrame) -> pd.Series:
    """XGBoost modelidan shubhali ehtimollik (0–1). Model yo'q bo'lsa None."""
    bundle = _load_model(os.path.join("models", "xgboost_model.pkl"))
    if bundle is None or not isinstance(bundle, dict) or "model" not in bundle:
        return None
    saved_feats = [f for f in bundle.get("features", ML_FEATURES) if f in df.columns]
    X_scaled    = _prepare_X(df, saved_feats, bundle.get("scaler"))
    probs = bundle["model"].predict_proba(X_scaled)[:, 1]
    return pd.Series(probs, index=df.index)


def assign_risk_level(scores: pd.Series) -> pd.Series:
    p98 = scores.quantile(0.98)
    p90 = scores.quantile(0.90)
    p60 = scores.quantile(0.60)
    def _classify(s):
        if s >= p98:   return "KRITIK"
        elif s >= p90: return "YUQORI"
        elif s >= p60: return "O'RTA"
        else:          return "PAST"
    return scores.apply(_classify)


def build_reason(row) -> str:
    parts = []
    ratio = row.get("price_ratio", np.nan)
    if pd.notna(ratio):
        pct = int(round(ratio * 100))
        if ratio < 0.10:
            parts.append(f"Narx baholashning atigi {pct}% ({row.get('start_price',0):,.0f} vs {row.get('appraised_price',0):,.0f})")
        elif ratio < 0.70:
            parts.append(f"Narx baholashdan {100-pct}% past")
        elif ratio >= 0.999:
            parts.append("Chegirmasiz (start == appraised)")

    cnt = int(row.get("auction_count", 0))
    if cnt > 100:
        parts.append(f"{cnt}x qayta e'lon")
    elif cnt > 50:
        parts.append(f"{cnt}x qayta e'lon")
    elif cnt > 20:
        parts.append(f"{cnt}x qayta e'lon")

    if row.get("is_bankruptcy", 0):
        if row.get("no_discount", 0):
            parts.append("BANKROTLIK + chegirmasiz")
        else:
            parts.append("Bankrotlik")

    if row.get("is_k_savdo", 0):
        parts.append("K-SAVDO")

    if row.get("seller_is_heavy", 0):
        parts.append(f"Sotuvchi {int(row.get('seller_lot_count',0))} lot chiqargan")

    return " | ".join(parts) if parts else "Statistik anomaliya"


# ─── MAIN PIPELINE ───────────────────────────────────────────────────────────

def run_pipeline(
    input_path: Union[str, Path, io.BytesIO],
    filename: str = "",
    output_dir: str = "data",
    verbose: bool = True,
) -> dict:
    """
    Universal pipeline. CSV yoki Excel qabul qiladi.

    Returns:
        {
          "predictions": pd.DataFrame,
          "report": str,
          "stats": dict,
          "output_csv": str,   # saved file path
          "output_report": str # saved file path
        }
    """
    os.makedirs(output_dir, exist_ok=True)

    def log(msg):
        if verbose:
            sys.stderr.write(msg + "\n")

    log("1. Yuklanmoqda...")
    df = load_file(input_path, filename)
    log(f"   {len(df)} qator, {len(df.columns)} ustun topildi")

    log("2. Tozalanmoqda...")
    df = clean(df)
    log(f"   {len(df)} lot (duplikatsiz)")

    log("3. Featurelar...")
    df = add_features(df)

    log("4. Scoring...")
    df["rule_score"] = rule_score(df)
    df["iso_score"]  = iso_score(df)
    xgb_prob         = xgb_score(df)

    mms = MinMaxScaler()
    df["iso_norm"]  = mms.fit_transform(df[["iso_score"]]).flatten()
    df["rule_norm"] = df["rule_score"] / 10.0

    if xgb_prob is not None:
        # 3-model ensemble: qoidalar 40% + XGBoost 35% + IsolationForest 25%
        df["xgb_prob"]  = xgb_prob
        df["risk_score"] = (
            df["rule_norm"] * 0.40 +
            df["xgb_prob"]  * 0.35 +
            df["iso_norm"]  * 0.25
        ).round(4)
        log("   Ensemble: qoidalar×0.40 + XGBoost×0.35 + IsoForest×0.25")
    else:
        df["xgb_prob"]  = np.nan
        df["risk_score"] = (df["rule_norm"] * 0.55 + df["iso_norm"] * 0.45).round(4)
        log("   Ensemble: qoidalar×0.55 + IsoForest×0.45 (XGBoost yo'q)")

    df["risk_level"] = assign_risk_level(df["risk_score"])

    log("5. Izohlar...")
    df["why_flagged"] = df.apply(build_reason, axis=1)

    # Output
    out_cols = [
        "lot_number", "lot_url", "address", "district", "category",
        "property_type", "auction_settings", "seller_name",
        "start_price", "appraised_price", "price_ratio",
        "auction_count", "auction_date",
        "rule_score", "iso_score", "xgb_prob", "risk_score", "risk_level", "why_flagged",
        "price_below_10pct", "price_below_70pct", "no_discount",
        "is_bankruptcy", "bankruptcy_no_discount",
        "is_repeated", "is_very_repeated", "is_mega_repeated",
        "is_k_savdo", "seller_lot_count",
    ]
    avail  = [c for c in out_cols if c in df.columns]
    df_out = df[avail].sort_values("risk_score", ascending=False)

    # Stats
    lvl  = df["risk_level"].value_counts().to_dict()
    stats = {
        "total":    len(df),
        "kritik":   lvl.get("KRITIK", 0),
        "yuqori":   lvl.get("YUQORI", 0),
        "orta":     lvl.get("O'RTA", 0),
        "past":     lvl.get("PAST", 0),
        "score_p50":  round(df["risk_score"].quantile(0.50), 3),
        "score_p90":  round(df["risk_score"].quantile(0.90), 3),
        "score_p98":  round(df["risk_score"].quantile(0.98), 3),
        "score_max":  round(df["risk_score"].max(), 3),
        "bankruptcy_no_discount": int(df.get("bankruptcy_no_discount", pd.Series(0)).sum()),
        "price_below_10pct":  int(df.get("price_below_10pct",  pd.Series(0)).sum()),
        "price_below_70pct":  int(df.get("price_below_70pct",  pd.Series(0)).sum()),
        "no_discount":        int(df.get("no_discount",         pd.Series(0)).sum()),
        "repeated_100plus":   int(df.get("is_ultra_repeated",   pd.Series(0)).sum()),
    }

    # Report matn
    top20  = df_out.head(20)
    region = df["region"].iloc[0] if "region" in df.columns and len(df) else "Noma'lum"
    report_lines = [
        "=" * 70,
        f"AUKSIONWATCH — RED FLAG HISOBOT",
        f"Viloyat: {region}",
        f"Sana: {pd.Timestamp.now().strftime('%d.%m.%Y %H:%M')}",
        "=" * 70,
        f"\nJami lot: {stats['total']:,}",
        "",
        "RISK DARAJASI (kvantil asosida, top 2% = KRITIK):",
        f"  KRITIK  : {stats['kritik']:>6,} lot",
        f"  YUQORI  : {stats['yuqori']:>6,} lot",
        "  O'RTA   : {:>6,} lot".format(stats["orta"]),
        f"  PAST    : {stats['past']:>6,} lot",
        "",
        "ASOSIY SIGNALLAR:",
        f"  Narx < 10% baholashdan (juda kuchli) : {stats['price_below_10pct']:>6,}",
        f"  Narx < 70% baholashdan               : {stats['price_below_70pct']:>6,}",
        f"  Chegirmasiz (start==appraised)        : {stats['no_discount']:>6,}",
        f"  Bankrotlik + chegirmasiz              : {stats['bankruptcy_no_discount']:>6,}",
        f"  100+ marta qayta e'lon                : {stats['repeated_100plus']:>6,}",
        "",
        "TOP 20 ENG SHUBHALI LOT:",
        f"{'Lot':<12} {'Tuman':<22} {'Narx':>14} {'Bahola':>14} {'%':>5} {'N':>5}  Score  Sabab",
        "-" * 115,
    ]
    for _, row in top20.iterrows():
        ratio_pct = f"{row.get('price_ratio',0)*100:.0f}%" if pd.notna(row.get("price_ratio")) else "N/A"
        reason_s  = str(row.get("why_flagged", ""))[:40]
        report_lines.append(
            f"{str(row.get('lot_number','')):<12} "
            f"{str(row.get('district',''))[:20]:<22} "
            f"{row.get('start_price',0):>14,.0f} "
            f"{row.get('appraised_price',0):>14,.0f} "
            f"{ratio_pct:>5} "
            f"{int(row.get('auction_count',0)):>5}  "
            f"{row.get('risk_score',0):.3f}  "
            f"{reason_s}"
        )
    report = "\n".join(report_lines)

    # Faylga saqlash
    base      = Path(output_dir)
    csv_path  = str(base / "predictions.csv")
    rep_path  = str(base / "report.txt")
    df_out.to_csv(csv_path, index=False, encoding="utf-8-sig")
    with open(rep_path, "w", encoding="utf-8") as f:
        f.write(report)

    log(f"\nNatija: KRITIK={stats['kritik']} | YUQORI={stats['yuqori']}")
    log(f"Saqlandi: {csv_path}")

    return {
        "predictions": df_out,
        "report":      report,
        "stats":       stats,
        "output_csv":  csv_path,
        "output_report": rep_path,
    }
