"""
Qadam 1: e-auksion.uz sitemap'laridan lot ID'larni yig'ish va
stratified sample olish.

Ishlatish:
    python scripts/00_get_lot_ids.py
Natija:
    data/lot_ids_all.parquet   — barcha ID'lar
    data/lot_ids.parquet       — 10,000 ta stratified sample
"""

import os
import xml.etree.ElementTree as ET

import pandas as pd
import requests
from tqdm import tqdm

NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

SITEMAPS = [
    "https://e-auksion.uz/sitemap_new_lots_part1.xml",
    "https://e-auksion.uz/sitemap_new_lots_part2.xml",
    "https://e-auksion.uz/sitemap_new_lots_part3.xml",
]

SAMPLE_SIZE = 10_000
RANDOM_SEED = 42
DATA_DIR = "data"


def fetch_sitemap(url: str) -> list[dict]:
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    rows = []
    for u in root.findall("sm:url", NS):
        loc_el = u.find("sm:loc", NS)
        mod_el = u.find("sm:lastmod", NS)
        if loc_el is None or "lot_id=" not in (loc_el.text or ""):
            continue
        lot_id = int(loc_el.text.split("lot_id=")[1])
        lastmod = mod_el.text if mod_el is not None else None
        rows.append({"lot_id": lot_id, "lastmod": lastmod, "url": loc_el.text})
    return rows


def stratified_sample(df: pd.DataFrame, n: int, seed: int) -> pd.DataFrame:
    """Oylik stratified sample — har oydan teng ulush."""
    df = df.copy()
    df["lastmod"] = pd.to_datetime(df["lastmod"], errors="coerce")
    df["month_bucket"] = df["lastmod"].dt.to_period("M").astype(str)

    bucket_counts = df["month_bucket"].value_counts()
    n_buckets = len(bucket_counts)
    per_bucket = max(1, n // n_buckets)

    sampled = (
        df.groupby("month_bucket", group_keys=False)
        .apply(lambda g: g.sample(min(len(g), per_bucket), random_state=seed))
    )

    # Agar yetmasa, qolganini random to'ldirish
    if len(sampled) < n:
        remaining = df.drop(sampled.index)
        extra = remaining.sample(min(len(remaining), n - len(sampled)), random_state=seed)
        sampled = pd.concat([sampled, extra])

    return sampled.sample(min(len(sampled), n), random_state=seed).reset_index(drop=True)


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    all_rows = []
    for url in tqdm(SITEMAPS, desc="Sitemaplar"):
        try:
            rows = fetch_sitemap(url)
            all_rows.extend(rows)
            print(f"  {url}: {len(rows):,} lot")
        except Exception as e:
            print(f"  XATO {url}: {e}")

    df_all = pd.DataFrame(all_rows).drop_duplicates("lot_id")
    all_path = os.path.join(DATA_DIR, "lot_ids_all.parquet")
    df_all.to_parquet(all_path, index=False)
    print(f"\nJami: {len(df_all):,} lot -> {all_path}")

    df_sample = stratified_sample(df_all, SAMPLE_SIZE, RANDOM_SEED)
    sample_path = os.path.join(DATA_DIR, "lot_ids.parquet")
    df_sample.to_parquet(sample_path, index=False)
    print(f"Sample: {len(df_sample):,} lot -> {sample_path}")
    print("\nOylik taqsimlash:")
    print(df_sample["month_bucket"].value_counts().sort_index().to_string())


if __name__ == "__main__":
    main()
