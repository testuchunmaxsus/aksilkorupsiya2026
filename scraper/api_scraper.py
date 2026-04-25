"""Direct HTTP scraper — e-auksion.uz yashirin gateway API'sidan foydalanadi.

Endpoint: GET https://e-auksion.uz/api/front/lot-info?lot_id={id}&lang=uz
Qaytaradi: structured JSON — geo koordinata, narxlar, sotuvchi ID, hujjatlar va h.k.

Playwright'ga nisbatan 10-50x tezroq — headless browser kerakmas, oddiy HTTP.
Sniff_api.py orqali brauzer trafikidan topilgan.
"""
import asyncio
import json
import sys
import time
from pathlib import Path
import httpx

ROOT = Path(__file__).parent.parent
API_URL = "https://e-auksion.uz/api/front/lot-info"

# Headers — haqiqiy brauzerni taqlid qilish (anti-bot bloklarni oldini olish)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 AuksionWatch/0.2",
    "Accept": "application/json",
    "Accept-Language": "uz,en;q=0.9",
    "Referer": "https://e-auksion.uz/",
}


async def fetch_lot(client: httpx.AsyncClient, lot_id: int) -> dict | None:
    """Bitta lot uchun API so'rov — raw JSON qaytaradi yoki xato dict.

    Xato bo'lganda: {"lot_id": id, "error": "..."} — pipeline davom etadi.
    """
    try:
        r = await client.get(API_URL, params={"lot_id": lot_id, "lang": "uz"}, timeout=15)
        if r.status_code != 200:
            return {"lot_id": lot_id, "error": f"http_{r.status_code}"}
        data = r.json()
        # Bo'sh javob yoki ERROR markeri — lot o'chirilgan/yo'q
        if not data or "ERROR" in data or not data.get("id"):
            return {"lot_id": lot_id, "error": "empty"}
        # Manba URL'ni ham qo'shamiz (provenance)
        data["_url"] = f"https://e-auksion.uz/lot-view?lot_id={lot_id}"
        return data
    except (httpx.HTTPError, json.JSONDecodeError) as e:
        return {"lot_id": lot_id, "error": str(e)[:120]}


async def scrape_all(lot_ids: list[int], concurrency: int = 20) -> list[dict]:
    """Ko'p lotni parallel scrape qilish (asyncio + semaphore).

    concurrency=20 da ~30 lot/sek (e-auksion serverini bosib qo'ymasdan).
    Har 100 lotda progress + ETA ko'rsatadi.
    """
    sem = asyncio.Semaphore(concurrency)  # bir vaqtda max N ta so'rov
    results = []
    started = time.time()

    async with httpx.AsyncClient(headers=HEADERS, http2=False, follow_redirects=True) as client:

        async def worker(lot_id):
            # Semaphore ushlab turadi — concurrency limit'idan oshmaslik uchun
            async with sem:
                return await fetch_lot(client, lot_id)

        # Hamma task'ni navbatga qo'yamiz, asyncio.as_completed bilan natijalarni real-vaqt olamiz
        tasks = [asyncio.create_task(worker(i)) for i in lot_ids]
        for i, fut in enumerate(asyncio.as_completed(tasks), 1):
            results.append(await fut)
            # Progress + ETA log (har 100 lot)
            if i % 100 == 0:
                elapsed = time.time() - started
                rate = i / elapsed
                eta = (len(lot_ids) - i) / rate
                print(f"[api] {i}/{len(lot_ids)}  {rate:.1f} lot/s  ETA {eta:.0f}s")

    return results


async def main():
    """CLI — sitemap'dan ID'larni o'qib, batch scrape qiladi."""
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=500, help="Necha lot scrape qilish")
    p.add_argument("--ids-file", default=str(ROOT / "data" / "lot_ids.json"))
    p.add_argument("--out", default=str(ROOT / "data" / "lots_api.json"))
    p.add_argument("--concurrency", type=int, default=20)
    p.add_argument("--offset", type=int, default=0, help="Boshlash indeksi (resume)")
    args = p.parse_args()

    # Sitemap natijalaridan slice — ko'pincha random sample uchun mos
    ids_data = json.loads(Path(args.ids_file).read_text(encoding="utf-8"))
    lot_ids = [r["lot_id"] for r in ids_data[args.offset : args.offset + args.limit]]
    print(f"[api] scraping {len(lot_ids)} lots, concurrency={args.concurrency}")

    started = time.time()
    results = await scrape_all(lot_ids, concurrency=args.concurrency)
    elapsed = time.time() - started

    # JSON saqlash (UTF-8, indented)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(
        json.dumps(results, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    ok = sum(1 for r in results if "error" not in r)
    print(f"[api] done: {ok}/{len(results)} success in {elapsed:.1f}s ({ok/elapsed:.1f} lot/s)")
    print(f"      output: {args.out}")


if __name__ == "__main__":
    asyncio.run(main())
