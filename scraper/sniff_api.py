"""Capture all network requests when e-auksion.uz loads a lot page.

Goal: discover the gateway API endpoint(s) so we can scrape via plain HTTP
instead of headless browser (10-100x faster).
"""
import asyncio
import json
from collections import defaultdict
from playwright.async_api import async_playwright

LOT_ID = 23469523
URL = f"https://e-auksion.uz/lot-view?lot_id={LOT_ID}"


async def main():
    requests_log = []
    by_host = defaultdict(int)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await ctx.new_page()

        async def on_request(req):
            entry = {
                "method": req.method,
                "url": req.url,
                "type": req.resource_type,
                "headers": dict(await req.all_headers()),
                "post": req.post_data if req.method != "GET" else None,
            }
            requests_log.append(entry)
            from urllib.parse import urlparse
            host = urlparse(req.url).netloc
            by_host[host] += 1

        async def on_response(resp):
            try:
                if resp.request.resource_type in ("xhr", "fetch"):
                    body = None
                    try:
                        body = (await resp.text())[:500]
                    except Exception:
                        body = "(binary)"
                    print(f"\n[{resp.status}] {resp.request.method} {resp.url}")
                    print(f"   content-type: {resp.headers.get('content-type', '?')}")
                    if body:
                        print(f"   body[:500]: {body}")
            except Exception as e:
                print(f"resp error: {e}")

        page.on("request", on_request)
        page.on("response", on_response)

        print(f"[sniff] loading {URL}")
        await page.goto(URL, wait_until="networkidle", timeout=45000)
        await asyncio.sleep(3)
        await browser.close()

    print("\n" + "=" * 60)
    print("HOST SUMMARY")
    print("=" * 60)
    for h, n in sorted(by_host.items(), key=lambda x: -x[1]):
        print(f"  {n:4d}  {h}")

    print("\n" + "=" * 60)
    print("XHR/FETCH ONLY (likely API)")
    print("=" * 60)
    for r in requests_log:
        if r["type"] in ("xhr", "fetch"):
            print(f"  {r['method']:6} {r['url']}")
            if r.get("post"):
                print(f"         BODY: {r['post'][:200]}")

    # save full log
    from pathlib import Path
    out = Path(__file__).parent.parent / "data" / "api_sniff.json"
    out.write_text(json.dumps(requests_log, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"\n[sniff] full log: {out}")


if __name__ == "__main__":
    asyncio.run(main())
