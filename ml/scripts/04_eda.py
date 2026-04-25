"""
Qadam 7: EDA hisobot yaratish.

Ishlatish:
    python scripts/04_eda.py
Natija:
    data/eda_report.html
"""

import os
import warnings

import pandas as pd
from ydata_profiling import ProfileReport

warnings.filterwarnings("ignore")

DATA_DIR = "data"


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    feat_path = os.path.join(DATA_DIR, "lots_features.parquet")

    print(f"Yuklash: {feat_path}")
    df = pd.read_parquet(feat_path)

    # Embedding ustunini EDA'dan olib tashlash (hajm katta)
    df_eda = df.drop(columns=["description_emb", "raw_html", "images", "documents"], errors="ignore")

    print(f"EDA hisobot yaratilmoqda ({len(df_eda):,} qator, {len(df_eda.columns)} ustun)...")
    profile = ProfileReport(
        df_eda,
        title="AuksionWatch EDA — 10,000 Lot",
        explorative=True,
        correlations={"pearson": {"calculate": True}, "spearman": {"calculate": False}},
        missing_diagrams={"heatmap": True, "bar": True},
        samples={"head": 10, "tail": 10},
        progress_bar=True,
    )

    out_path = os.path.join(DATA_DIR, "eda_report.html")
    profile.to_file(out_path)
    print(f"Saqlandi: {out_path}")


if __name__ == "__main__":
    main()
