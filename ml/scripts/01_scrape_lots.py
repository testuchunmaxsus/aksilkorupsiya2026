"""
Qadam 3: Playwright bilan e-auksion.uz lot sahifalarini scrape qilish.

Ishlatish:
    python scripts/01_scrape_lots.py [--limit N] [--resume]
    python scripts/01_scrape_lots.py --limit 100   # test uchun
    python scripts/01_scrape_lots.py --resume       # to'xtagan joydan davom etish

Natija:
    data/lots_raw.parquet
    data/errors.jsonl
"""

import argparse
import asyncio
import json
import os
import re
import time
from datetime import datetime

import pandas as pd
from playwright.async_api import Browser, BrowserContext, Page, async_playwright
from tenacity import retry, stop_after_attempt, wait_exponential

DATA_DIR = "data"
CHECKPOINT_EVERY = 100
CONCURRENCY = 5
SLEEP_BETWEEN = 0.3  # sekund
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


def _parse_number(text: str | None) -> str | None:
    if not text:
        return None
    return re.sub(r"[^\d.]", "", text).strip() or None


def _safe_text(val: str | None) -> str | None:
    return val.strip() if val else None


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
async def scrape_lot(page: Page, lot_id: int) -> dict:
    url = f"https://e-auksion.uz/lot-view?lot_id={lot_id}"
    await page.goto(url, wait_until="networkidle", timeout=30_000)

    # Vue SPA kontenti yuklanishini kutish
    try:
        await page.wait_for_selector(
            ".lot-view, [class*='lot-detail'], [class*='lot-info'], main",
            timeout=15_000,
        )
    except Exception:
        pass  # raw_html saqlab davom etish

    async def get_text(selector: str) -> str | None:
        try:
            el = page.locator(selector).first
            if await el.count() == 0:
                return None
            return _safe_text(await el.text_content(timeout=3_000))
        except Exception:
            return None

    async def get_attr(selector: str, attr: str) -> str | None:
        try:
            el = page.locator(selector).first
            if await el.count() == 0:
                return None
            return await el.get_attribute(attr, timeout=3_000)
        except Exception:
            return None

    async def get_all_attrs(selector: str, attr: str) -> list[str]:
        try:
            els = page.locator(selector)
            count = await els.count()
            return [
                v for i in range(count)
                if (v := await els.nth(i).get_attribute(attr, timeout=2_000))
            ]
        except Exception:
            return []

    async def js_window_state() -> dict:
        try:
            return await page.evaluate(
                "() => {"
                "  const s = window.__INITIAL_STATE__ || window.__nuxt__ || {};"
                "  return JSON.parse(JSON.stringify(s));"
                "}"
            )
        except Exception:
            return {}

    # Koordinatlar JSON'dan
    geo_lat, geo_lon = None, None
    try:
        map_el = page.locator("[data-lat], [data-lng]").first
        if await map_el.count() > 0:
            geo_lat = await map_el.get_attribute("data-lat")
            geo_lon = await map_el.get_attribute("data-lng")
    except Exception:
        pass

    raw_html = await page.content()

    return {
        "lot_id": lot_id,
        "url": url,
        "scraped_at": datetime.utcnow().isoformat(),
        "lot_number": await get_text(".lot-number, [class*='lot-id'], [class*='lot-number']"),
        "lot_type": await get_text(".lot-type, [class*='property-type'], [class*='lot-type']"),
        "region": await get_text(".lot-region, [class*='region-name'], [class*='region']"),
        "district": await get_text(".lot-district, [class*='district']"),
        "address": await get_text(".lot-address, [class*='address']"),
        "area_m2": _parse_number(await get_text(".lot-area, [class*='area']")),
        "start_price": _parse_number(await get_text(".start-price, [class*='start-price'], [class*='startPrice']")),
        "current_price": _parse_number(await get_text(".current-price, [class*='current-price'], [class*='soldPrice']")),
        "auction_type": await get_text(".auction-type, [class*='auction-type'], [class*='auctionType']"),
        "bidders_count": _parse_number(await get_text(".bidders-count, [class*='participants'], [class*='bidders']")),
        "seller_name": await get_text(".seller-name, [class*='seller'] .name, [class*='sellerName']"),
        "seller_inn": await get_text(".seller-inn, [class*='seller'] .inn, [class*='sellerInn']"),
        "start_time": await get_text(".auction-start, [class*='start-date'], [class*='startDate']"),
        "end_time": await get_text(".auction-end, [class*='end-date'], [class*='endDate']"),
        "status": await get_text(".lot-status, [class*='status']"),
        "winner_inn": await get_text(".winner-inn, [class*='winner'] .inn, [class*='winnerInn']"),
        "description": await get_text(".lot-description, [class*='description']"),
        "geo_lat": geo_lat,
        "geo_lon": geo_lon,
        "images": await get_all_attrs(".lot-images img, [class*='gallery'] img", "src"),
        "documents": await get_all_attrs("a[href*='.pdf'], [class*='documents'] a", "href"),
        "raw_html": raw_html,
    }


async def worker(
    ctx: BrowserContext,
    lot_ids: list[int],
    results: list[dict],
    errors: list[dict],
    semaphore: asyncio.Semaphore,
    pbar_queue: asyncio.Queue,
):
    for lot_id in lot_ids:
        async with semaphore:
            page = await ctx.new_page()
            try:
                data = await scrape_lot(page, lot_id)
                results.append(data)
            except Exception as e:
                errors.append({"lot_id": lot_id, "error": str(e), "ts": datetime.utcnow().isoformat()})
            finally:
                await page.close()
                await asyncio.sleep(SLEEP_BETWEEN)
                await pbar_queue.put(1)


async def progress_reporter(queue: asyncio.Queue, total: int, results: list, errors: list):
    done = 0
    start = time.time()
    while done < total:
        await queue.get()
        done += 1
        if done % CHECKPOINT_EVERY == 0 or done == total:
            elapsed = time.time() - start
            rate = done / elapsed if elapsed > 0 else 0
            eta = (total - done) / rate if rate > 0 else 0
            print(
                f"  [{done}/{total}] ok={len(results)} err={len(errors)} "
                f"rate={rate:.1f}/s eta={eta/60:.1f}min"
            )
            if results:
                pd.DataFrame(results).to_parquet(
                    os.path.join(DATA_DIR, "lots_raw.parquet"), index=False
                )


async def main(limit: int | None, resume: bool):
    os.makedirs(DATA_DIR, exist_ok=True)

    df_ids = pd.read_parquet(os.path.join(DATA_DIR, "lot_ids.parquet"))
    lot_ids = df_ids["lot_id"].tolist()

    if resume and os.path.exists(os.path.join(DATA_DIR, "lots_raw.parquet")):
        done_ids = set(
            pd.read_parquet(os.path.join(DATA_DIR, "lots_raw.parquet"))["lot_id"].tolist()
        )
        lot_ids = [x for x in lot_ids if x not in done_ids]
        print(f"Resume: {len(done_ids)} tayyor, {len(lot_ids)} qoldi")

    if limit:
        lot_ids = lot_ids[:limit]

    print(f"Scrape qilinadigan lot: {len(lot_ids):,}")

    results: list[dict] = []
    errors: list[dict] = []

    if resume and os.path.exists(os.path.join(DATA_DIR, "lots_raw.parquet")):
        results = pd.read_parquet(os.path.join(DATA_DIR, "lots_raw.parquet")).to_dict("records")

    semaphore = asyncio.Semaphore(CONCURRENCY)
    pbar_queue: asyncio.Queue = asyncio.Queue()

    # Lot ID'larni CONCURRENCY ta guruhga bo'lish
    chunks = [lot_ids[i::CONCURRENCY] for i in range(CONCURRENCY)]

    async with async_playwright() as p:
        browser: Browser = await p.chromium.launch(headless=True)
        ctx: BrowserContext = await browser.new_context(
            user_agent=USER_AGENTS[0],
            viewport={"width": 1280, "height": 800},
            java_script_enabled=True,
        )

        tasks = [
            worker(ctx, chunk, results, errors, semaphore, pbar_queue)
            for chunk in chunks
        ] + [progress_reporter(pbar_queue, len(lot_ids), results, errors)]

        await asyncio.gather(*tasks)
        await browser.close()

    # Final saqlash
    if results:
        pd.DataFrame(results).to_parquet(os.path.join(DATA_DIR, "lots_raw.parquet"), index=False)
        print(f"\nSaqlandi: {len(results):,} lot → data/lots_raw.parquet")

    if errors:
        with open(os.path.join(DATA_DIR, "errors.jsonl"), "w", encoding="utf-8") as f:
            for e in errors:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
        print(f"Xatolar: {len(errors):,} → data/errors.jsonl")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Sinov uchun cheklov")
    parser.add_argument("--resume", action="store_true", help="To'xtagan joydan davom etish")
    args = parser.parse_args()
    asyncio.run(main(args.limit, args.resume))
