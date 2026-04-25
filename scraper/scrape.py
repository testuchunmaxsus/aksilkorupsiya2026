"""Playwright scraper for e-auksion.uz lot pages.

Each lot page is a Vue SPA — needs headless browser + wait for hydration.
"""
import asyncio
import json
import re
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

LOT_URL = "https://e-auksion.uz/lot-view?lot_id={lot_id}"
OUT_PATH = Path(__file__).parent.parent / "data" / "lots_raw.json"


async def extract_lot(page, lot_id: int) -> dict | None:
    url = LOT_URL.format(lot_id=lot_id)
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        # Vue SPA: wait for content to hydrate
        await page.wait_for_function(
            "document.querySelector('#q-app') && document.querySelector('#q-app').innerHTML.length > 1000",
            timeout=20000,
        )
        await asyncio.sleep(1.5)  # extra render time

        # Strategy: parse all visible text, extract structured fields by labels
        text_dump = await page.evaluate(
            """() => {
                const root = document.querySelector('#q-app');
                if (!root) return '';
                return root.innerText;
            }"""
        )
        title = await page.title()
        html = await page.content()

        return {
            "lot_id": lot_id,
            "url": url,
            "title": title,
            "text": text_dump,
            "html_length": len(html),
        }
    except PWTimeout:
        return {"lot_id": lot_id, "url": url, "error": "timeout"}
    except Exception as e:
        return {"lot_id": lot_id, "url": url, "error": str(e)[:200]}


async def scrape(lot_ids: list[int], concurrency: int = 4) -> list[dict]:
    results = []
    sem = asyncio.Semaphore(concurrency)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 800},
        )

        async def worker(lot_id):
            async with sem:
                page = await ctx.new_page()
                try:
                    data = await extract_lot(page, lot_id)
                    return data
                finally:
                    await page.close()

        tasks = [worker(i) for i in lot_ids]
        for i, fut in enumerate(asyncio.as_completed(tasks), 1):
            r = await fut
            results.append(r)
            if i % 10 == 0:
                print(f"[scrape] {i}/{len(lot_ids)} done")
                OUT_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

        await browser.close()
    return results


async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--ids-file", default=str(Path(__file__).parent.parent / "data" / "lot_ids.json"))
    parser.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args()

    ids_data = json.loads(Path(args.ids_file).read_text())
    lot_ids = [r["lot_id"] for r in ids_data[: args.limit]]
    print(f"[scrape] starting {len(lot_ids)} lots, concurrency={args.concurrency}")

    results = await scrape(lot_ids, concurrency=args.concurrency)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    ok = sum(1 for r in results if "error" not in r)
    print(f"[scrape] done: {ok}/{len(results)} success -> {OUT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
