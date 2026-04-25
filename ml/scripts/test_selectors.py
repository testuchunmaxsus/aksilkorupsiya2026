"""
Bitta lot sahifasini ochib, barcha mavjud element va ma'lumotlarni topish.
python scripts/test_selectors.py
"""
import asyncio, json
from playwright.async_api import async_playwright

TEST_LOT = 23469523

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"
        )
        page = await ctx.new_page()
        url = f"https://e-auksion.uz/lot-view?lot_id={TEST_LOT}"
        print(f"Opening: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(5000)  # Vue render kutish

        # Barcha matnli elementlarni yig'ish
        elements = await page.evaluate("""() => {
            const results = [];
            const all = document.querySelectorAll('*');
            for (const el of all) {
                const text = el.innerText?.trim();
                if (text && text.length > 2 && text.length < 300 && el.children.length === 0) {
                    results.push({
                        tag: el.tagName,
                        class: el.className,
                        id: el.id,
                        text: text.substring(0, 100)
                    });
                }
            }
            return results.slice(0, 200);
        }""")

        print(f"\n--- Matnli elementlar ({len(elements)} ta) ---")
        out_lines = []
        for el in elements:
            cls = el['class'][:40] if el['class'] else ''
            line = f"  [{el['tag']}] class='{cls}' id='{el['id']}' => '{el['text']}'"
            out_lines.append(line)
        with open("data/elements.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(out_lines))
        print("Elements saqlandi: data/elements.txt")

        # Window state
        state = await page.evaluate("""() => {
            try { return JSON.stringify(window.__INITIAL_STATE__ || window.__vue_store__ || {}) }
            catch(e) { return '{}' }
        }""")
        if len(state) > 2:
            with open("data/window_state.json", "w", encoding="utf-8") as f:
                f.write(state)
            print(f"\nWindow state saqlandi: data/window_state.json ({len(state)} bytes)")

        # Network requests
        # API so'rovlarni ushlash
        api_urls = []
        api_responses = {}

        async def capture_response(response):
            url = response.url
            if any(x in url for x in ["/api/", "lot", "auction", ".json"]):
                api_urls.append(url)
                try:
                    body = await response.text()
                    api_responses[url] = body[:2000]
                except Exception:
                    pass

        page.on("response", capture_response)
        await page.reload(wait_until="domcontentloaded")
        await page.wait_for_timeout(4000)

        with open("data/api_urls.txt", "w", encoding="utf-8") as f:
            for u in api_urls[:30]:
                f.write(u + "\n")
        print(f"\nAPI so'rovlar saqlandi: data/api_urls.txt ({len(api_urls)} ta)")

        with open("data/api_responses.json", "w", encoding="utf-8") as f:
            json.dump(api_responses, f, ensure_ascii=False, indent=2)
        print("API responses: data/api_responses.json")

        # HTML saqlash
        html = await page.content()
        with open("data/sample_lot.html", "w", encoding="utf-8") as f:
            f.write(html)
        print(f"\nHTML saqlandi: data/sample_lot.html ({len(html):,} bytes)")

        await browser.close()

asyncio.run(main())
