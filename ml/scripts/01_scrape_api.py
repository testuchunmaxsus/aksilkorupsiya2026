"""
Optimallashtirilgan API scraper: 30 parallel -> 10K lot ~10 daqiqada.

Ishlatish:
    python scripts/01_scrape_api.py
    python scripts/01_scrape_api.py --limit 500
    python scripts/01_scrape_api.py --resume
"""

import argparse
import asyncio
import json
import os
import sys
import time

import aiohttp
import pandas as pd
from tqdm import tqdm

DATA_DIR = "data"
API_BASE = "https://e-auksion.uz/api/front/lot-info"
CONCURRENCY = 30
SLEEP_MS = 0.02
CHECKPOINT_EVERY = 500
TIMEOUT = aiohttp.ClientTimeout(total=20, connect=5)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://e-auksion.uz/",
}

REGION_CODE = {
    1: "UZ-TK", 2: "UZ-AN", 3: "UZ-BU", 4: "UZ-FA",
    5: "UZ-JI", 6: "UZ-XO", 7: "UZ-NG", 8: "UZ-NW",
    9: "UZ-QA", 10: "UZ-QR", 11: "UZ-SA", 12: "UZ-SI",
    13: "UZ-SU", 14: "UZ-TO",
}

STATUS_MAP = {1: "upcoming", 2: "active", 3: "active", 4: "completed",
              5: "cancelled", 6: "cancelled", 7: "cancelled"}


def _uz(obj) -> str:
    if not obj:
        return ""
    if isinstance(obj, dict):
        return str(obj.get("name_uz") or obj.get("name_ru") or obj.get("name_en") or "")
    return str(obj)


def parse_lot(d: dict) -> dict:
    images = [i["media_url"] for i in (d.get("confiscant_images_list") or []) if i.get("media_url")]
    docs = [i["file_name"] for i in (d.get("confiscant_documents_list") or []) if i.get("file_name")]
    c = d.get("c_user") or {}
    rid = d.get("regions_id") or 0

    return {
        "lot_id":             d.get("id"),
        "lot_number":         d.get("lot_number"),
        "name":               d.get("name"),
        "start_price":        d.get("start_price"),
        "current_price":      d.get("current_price"),
        "appraised_price":    d.get("baholangan_narx"),
        "min_price":          d.get("min_summa"),
        "step_percent":       d.get("step_percent"),
        "step_summa":         d.get("step_summa"),
        "zaklad_summa":       d.get("zaklad_summa"),
        "zaklad_percent":     d.get("zaklad_percent"),
        "geo_lat":            d.get("lat"),
        "geo_lon":            d.get("lng"),
        "regions_id":         rid,
        "region_code":        REGION_CODE.get(rid),
        "region":             _uz(d.get("region_name")),
        "district":           _uz(d.get("area_name")),
        "address":            d.get("joylashgan_manzil"),
        "is_closed":          int(d.get("is_closed") or 0),
        "auction_type":       "closed" if d.get("is_closed") else "open",
        "is_descending":      int(d.get("is_descending_auction") or 0),
        "lot_statuses_id":    d.get("lot_statuses_id"),
        "status":             STATUS_MAP.get(d.get("lot_statuses_id") or 0, "unknown"),
        "lot_type":           d.get("lot_type"),
        "property_group":     _uz(d.get("confiscant_groups_name")),
        "property_category":  _uz(d.get("confiscant_categories_name")),
        "order_cnt":          d.get("order_cnt"),
        "auction_cnt":        d.get("auction_cnt"),
        "view_count":         d.get("view_count"),
        "start_time":         d.get("start_time_str"),
        "order_end_time":     d.get("order_end_time_str"),
        "create_time":        d.get("create_time"),
        "seller_user_id":     d.get("c_users_id"),
        "seller_name":        c.get("name"),
        "seller_phone":       c.get("phone"),
        "seller_email":       c.get("email"),
        "seller_region":      c.get("region_name"),
        "seller_inn":         d.get("mib_inn"),
        "is_from_mib":        int(d.get("is_from_mib_portal") or 0),
        "mib_name":           d.get("mib_name"),
        "exec_order_type_id": d.get("exec_order_types_id"),
        "additional_info":    d.get("additional_info"),
        "images_count":       len(images),
        "docs_count":         len(docs),
        "images":             json.dumps(images[:5], ensure_ascii=False),
        "docs":               json.dumps(docs[:5], ensure_ascii=False),
    }


async def fetch_one(session: aiohttp.ClientSession, lot_id: int, sem: asyncio.Semaphore) -> dict | None:
    url = f"{API_BASE}?lot_id={lot_id}&lang=uz"
    async with sem:
        for _ in range(3):
            try:
                async with session.get(url, headers=HEADERS, timeout=TIMEOUT) as resp:
                    if resp.status == 200:
                        data = await resp.json(content_type=None)
                        return parse_lot(data)
                    if resp.status == 404:
                        return None
                    if resp.status == 429:
                        await asyncio.sleep(5)
            except Exception:
                await asyncio.sleep(1)
        return None


async def run(lot_ids: list[int], resume_results: list[dict]) -> list[dict]:
    results = list(resume_results)
    sem = asyncio.Semaphore(CONCURRENCY)
    conn = aiohttp.TCPConnector(ssl=False, limit=CONCURRENCY + 10)
    raw_path = os.path.join(DATA_DIR, "lots_raw.parquet")
    start = time.time()

    async with aiohttp.ClientSession(connector=conn) as sess:
        tasks = [fetch_one(sess, lid, sem) for lid in lot_ids]
        done = 0

        with tqdm(total=len(lot_ids), unit="lot", file=sys.stderr) as pbar:
            for coro in asyncio.as_completed(tasks):
                row = await coro
                if row:
                    results.append(row)
                done += 1
                pbar.update(1)
                await asyncio.sleep(SLEEP_MS)

                if done % CHECKPOINT_EVERY == 0:
                    elapsed = time.time() - start
                    rate = done / elapsed if elapsed > 0 else 1
                    pbar.set_postfix(ok=len(results), rate=f"{rate:.0f}/s")
                    pd.DataFrame(results).to_parquet(raw_path, index=False)

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    os.makedirs(DATA_DIR, exist_ok=True)
    raw_path = os.path.join(DATA_DIR, "lots_raw.parquet")

    df_ids = pd.read_parquet(os.path.join(DATA_DIR, "lot_ids.parquet"))
    lot_ids = df_ids["lot_id"].tolist()

    resume_results: list[dict] = []
    if args.resume and os.path.exists(raw_path):
        existing = pd.read_parquet(raw_path)
        resume_results = existing.to_dict("records")
        done_set = set(existing["lot_id"].tolist())
        lot_ids = [x for x in lot_ids if x not in done_set]
        sys.stderr.write(f"Resume: {len(resume_results)} tayyor, {len(lot_ids)} qoldi\n")

    if args.limit:
        lot_ids = lot_ids[: args.limit]

    sys.stderr.write(f"Scrape: {len(lot_ids)} lot | concurrency={CONCURRENCY}\n")

    results = asyncio.run(run(lot_ids, resume_results))

    df = pd.DataFrame(results).drop_duplicates("lot_id") if results else pd.DataFrame()
    if not df.empty:
        df.to_parquet(raw_path, index=False)
        elapsed = time.time()
        sys.stderr.write(f"Saqlandi: {len(df)} lot -> {raw_path}\n")
        sys.stderr.write(f"Ustunlar: {len(df.columns)}\n")


if __name__ == "__main__":
    main()
