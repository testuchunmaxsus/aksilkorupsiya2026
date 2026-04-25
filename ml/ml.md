# ML Engineer uchun VAZIFA: Dataset yig'ish (1-bosqich)

**Loyiha:** AuksionWatch
**Bosqich:** 1 — MVP Dataset (24 soat ichida tugatilishi shart)
**Manba:** e-auksion.uz
**Maqsad:** AI red-flag detector'ni o'qitish va validatsiya qilish uchun **toza, structured 10,000 lotlik dataset** yaratish

---

## 0. TUSHUNTIRISH (oldindan o'qing)

E-auksion.uz — Vue SPA. HTML server'dan bo'sh keladi (faqat `<div id="q-app">`). Demak **oddiy `requests` ishlamaydi** — Playwright (yoki Selenium) kerak.

LEKIN: sitemap'da 23M+ lot ID public, va `lot-view?lot_id=X` sahifasi headless browser bilan 100% ochiladi.

Bizning maqsad — **ML uchun toza CSV/Parquet** yaratish. Backend API'ni boshqa odam yozadi.

---

## 1. DELIVERABLE (siz nima topshirasiz)

24 soat ichida quyidagilarni `data/` papkaga topshirasiz:

| Fayl | Hajm | Format | Mazmuni |
|---|---|---|---|
| `lots_raw.parquet` | ~10,000 qator | Parquet | Scrape qilingan xom ma'lumot |
| `lots_clean.parquet` | ~10,000 qator | Parquet | Tozalangan, normalizatsiya qilingan |
| `lots_features.parquet` | ~10,000 qator | Parquet | ML uchun feature'lar |
| `red_flags_labeled.csv` | ~200 qator | CSV | Qo'lda yorliqlangan ground-truth |
| `eda_report.html` | 1 fayl | HTML | EDA hisobot (pandas-profiling) |
| `scrape_lots.py` | Skript | Python | Reproducible scraping |
| `notebook_eda.ipynb` | Notebook | Jupyter | Tahlil va vizualizatsiya |

---

## 2. KETMA-KETLIK (qadamlar)

### Qadam 1 — Sitemap'dan lot ID'larni olish (30 daq)

```python
# scripts/00_get_lot_ids.py
import requests, xml.etree.ElementTree as ET
import pandas as pd

NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
sitemaps = [
    "https://e-auksion.uz/sitemap_new_lots_part1.xml",
    "https://e-auksion.uz/sitemap_new_lots_part2.xml",
    "https://e-auksion.uz/sitemap_new_lots_part3.xml",
]

ids = []
for url in sitemaps:
    r = requests.get(url, timeout=30)
    root = ET.fromstring(r.content)
    for u in root.findall("sm:url", NS):
        loc = u.find("sm:loc", NS).text
        lastmod = u.find("sm:lastmod", NS).text
        lot_id = int(loc.split("lot_id=")[1])
        ids.append({"lot_id": lot_id, "lastmod": lastmod, "url": loc})

df = pd.DataFrame(ids)
df.to_parquet("data/lot_ids.parquet")
print(f"Total: {len(df)}")
```

**Natija:** ~23M lot ID. **Random sample 10,000 ta tanlang** (stratified by `lastmod` oyiga).

### Qadam 2 — 1 ta lotni qo'lda tahlil qiling (1 soat)

Brauzerda oching:
```
https://e-auksion.uz/lot-view?lot_id=23469523
```

**Topshiriq:** Quyidagi ma'lumotlarni qaysi DOM selektordan olish mumkinligini aniqlang va `selectors.md` ga yozing:

| Maydon | Selector | Misol qiymat |
|---|---|---|
| `lot_number` | ? | "№23469523" |
| `lot_type` | ? | "yer uchastkasi" |
| `region` | ? | "Toshkent shahri" |
| `district` | ? | "Yunusobod tumani" |
| `address` | ? | "..." |
| `area_m2` | ? | 1500 |
| `start_price` | ? | 250000000 |
| `current_price` | ? | 280000000 |
| `auction_type` | ? | "ochiq" / "yopiq" |
| `bidders_count` | ? | 3 |
| `seller_name` | ? | "Davaktiv" |
| `seller_inn` | ? | "201234567" |
| `start_time` | ? | "2026-04-20 10:00" |
| `end_time` | ? | "2026-04-25 18:00" |
| `status` | ? | "tugagan" / "davom etmoqda" / "kelgusi" |
| `winner_inn` | ? | "..." |
| `description` | ? | "..." |
| `geo_lat`, `geo_lon` | ? | 41.31, 69.27 |
| `images` | ? | [url1, url2] |
| `documents` | ? | [pdf_url1, ...] |

### Qadam 3 — Playwright scraper (3 soat)

```python
# scripts/01_scrape_lots.py
import asyncio
from playwright.async_api import async_playwright
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
async def scrape_lot(page, lot_id):
    await page.goto(f"https://e-auksion.uz/lot-view?lot_id={lot_id}",
                    wait_until="networkidle", timeout=30000)
    # Vue SPA — selektorlar yuklanishini kuting
    await page.wait_for_selector(".lot-info, .lot-detail", timeout=15000)
    return {
        "lot_id": lot_id,
        "lot_type": await page.locator("...").text_content(),
        # qadam 2 da topgan selektorlaringizni qo'ying
        ...
        "raw_html": await page.content()
    }

async def main():
    ids = pd.read_parquet("data/lot_ids.parquet").sample(10000, random_state=42)
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(user_agent="Mozilla/5.0 ...")
        for i, row in enumerate(ids.itertuples()):
            try:
                page = await ctx.new_page()
                data = await scrape_lot(page, row.lot_id)
                results.append(data)
                await page.close()
                if i % 100 == 0:
                    print(f"{i}/10000")
                    pd.DataFrame(results).to_parquet("data/lots_raw.parquet")
                await asyncio.sleep(0.5)  # rate limit
            except Exception as e:
                print(f"Error {row.lot_id}: {e}")
        await browser.close()
    pd.DataFrame(results).to_parquet("data/lots_raw.parquet")

asyncio.run(main())
```

**Tavsiya:**
- 5 ta concurrent page (asyncio.gather, semaphore=5) → ~1 soatda 10K lot
- Har 100 lot dan keyin checkpoint saqlang (crash bo'lsa)
- IP bloklansa: Bright Data / IPRoyal proxy ishlating, yoki VPN

### Qadam 4 — Cleaning + Normalization (3 soat)

```python
# scripts/02_clean.py
df = pd.read_parquet("data/lots_raw.parquet")

# Narx → integer (so'm)
df["start_price"] = df["start_price"].str.replace(r"[^\d]", "", regex=True).astype("Int64")

# Sana → datetime
df["start_time"] = pd.to_datetime(df["start_time"], errors="coerce")

# Region → standart kod (UZ-TK, UZ-FA, ...)
REGION_MAP = {"Toshkent shahri": "UZ-TK", "Farg'ona": "UZ-FA", ...}
df["region_code"] = df["region"].map(REGION_MAP)

# Auction type → enum
df["auction_type"] = df["auction_type"].str.lower().map({
    "ochiq": "open", "очиқ": "open", "yopiq": "closed", "ёпиқ": "closed"
})

# Geocoding (Nominatim) — manzilsiz lotlar uchun
# rate limit: 1/sec

# INN normalize: 9 digit, leading zeros saqlash
df["seller_inn"] = df["seller_inn"].str.zfill(9)

df.to_parquet("data/lots_clean.parquet")
```

### Qadam 5 — Feature Engineering (4 soat)

ML model uchun feature'lar:

```python
# scripts/03_features.py
df = pd.read_parquet("data/lots_clean.parquet")

# 1. NARX FEATURE'LARI
df["price_per_m2"] = df["sold_price"] / df["area_m2"]
df["discount_pct"] = (df["start_price"] - df["sold_price"]) / df["start_price"] * 100
df["price_log"] = np.log1p(df["sold_price"])

# 2. AUKSION FEATURE'LARI
df["is_closed"] = (df["auction_type"] == "closed").astype(int)
df["is_single_bidder"] = (df["bidders_count"] == 1).astype(int)
df["bidders_log"] = np.log1p(df["bidders_count"])

# 3. VAQT FEATURE'LARI
df["duration_hours"] = (df["end_time"] - df["start_time"]).dt.total_seconds() / 3600
df["is_short_duration"] = (df["duration_hours"] < 24).astype(int)
df["start_hour"] = df["start_time"].dt.hour
df["start_weekday"] = df["start_time"].dt.weekday
df["is_weekend"] = df["start_weekday"].isin([5, 6]).astype(int)

# 4. SOTUVCHI FEATURE'LARI (group-by)
seller_stats = df.groupby("seller_inn").agg(
    seller_total_lots=("lot_id", "count"),
    seller_avg_discount=("discount_pct", "mean"),
    seller_closed_pct=("is_closed", "mean")
).reset_index()
df = df.merge(seller_stats, on="seller_inn", how="left")

# 5. G'OLIB FEATURE'LARI
winner_stats = df.groupby("winner_inn").agg(
    winner_total_wins=("lot_id", "count"),
    winner_unique_sellers=("seller_inn", "nunique")
).reset_index()
winner_stats["winner_seller_concentration"] = (
    winner_stats["winner_total_wins"] / winner_stats["winner_unique_sellers"]
)
df = df.merge(winner_stats, on="winner_inn", how="left")

# 6. NARX BENCHMARK (median by region+type+area_bin)
df["area_bin"] = pd.cut(df["area_m2"], bins=[0, 100, 500, 1000, 5000, 1e6])
benchmark = df.groupby(["region_code", "lot_type", "area_bin"])["price_per_m2"].median().reset_index()
benchmark.columns = [..., "benchmark_price_per_m2"]
df = df.merge(benchmark, on=["region_code", "lot_type", "area_bin"], how="left")
df["price_z_score"] = (df["price_per_m2"] - df["benchmark_price_per_m2"]) / df["price_per_m2"].std()
df["price_anomaly"] = (df["price_z_score"].abs() > 2).astype(int)

# 7. TEXT EMBEDDING (description)
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("intfloat/multilingual-e5-small")
df["description_emb"] = model.encode(df["description"].fillna("").tolist()).tolist()

df.to_parquet("data/lots_features.parquet")
```

### Qadam 6 — Qo'lda yorliqlash: 200 ta lot (3 soat)

ML model'ni baholash uchun **ground-truth** kerak.

`label_lots.csv` (200 qator):

| lot_id | is_suspicious | flag_type | comment |
|---|---|---|---|
| 12345678 | 1 | closed_low_price | Yopiq + 50% diskont |
| 12345679 | 0 | normal | Sotilmagan, normal |
| 12345680 | 1 | single_bidder_concentration | 1 ishtirokchi + sotuvchi 80% lotni shu firmaga sotgan |
| ... | | | |

**Strategiya:**
- 100 ta random sample
- 50 ta yopiq auksion (closed)
- 50 ta `discount_pct > 30` lotlar (shubhali)
- Har birini brauzerda oching, qaror qiling

### Qadam 7 — EDA hisobot (2 soat)

```python
# scripts/04_eda.py
from ydata_profiling import ProfileReport
df = pd.read_parquet("data/lots_features.parquet")
profile = ProfileReport(df, title="AuksionWatch EDA", explorative=True)
profile.to_file("data/eda_report.html")
```

**Qo'shimcha vizualizatsiyalar (Jupyter notebookda):**
1. Viloyat bo'yicha lotlar soni (bar chart)
2. Ochiq vs yopiq auksion narx taqsimoti (boxplot)
3. Bidders_count gistogrammasi
4. discount_pct gistogrammasi (red flag oynasi: > 30%)
5. Top 10 sotuvchi (lot soni bo'yicha)
6. Top 10 g'olib (yutuq soni bo'yicha)
7. Sotuvchi-g'olib graf (NetworkX, top-50 firma)
8. Geo-xarita: lotlar joylashuvi (folium)
9. Sana bo'yicha trend (line chart)
10. Korrelyatsiya matritsa (heatmap)

### Qadam 8 — Validatsiya checklist (1 soat)

Topshirishdan oldin tekshiring:

- [ ] `lots_raw.parquet` da 9000+ qator bor
- [ ] Maydonlarning > 80% to'ldirilgan
- [ ] Narx maydoni numeric, NaN < 5%
- [ ] Sana maydoni datetime, NaN < 5%
- [ ] `region_code` standart kod (UZ-XX)
- [ ] `auction_type` faqat ["open", "closed"]
- [ ] Duplikatlar yo'q (`lot_id` unique)
- [ ] `lots_features.parquet` da 30+ feature
- [ ] `red_flags_labeled.csv` da 200 ta yorliq
- [ ] `eda_report.html` ochiladi va o'qiladi
- [ ] `scrape_lots.py` reproducible (random seed)
- [ ] README.md ga ishga tushirish yo'riqnomasi yozilgan

---

## 3. PROBLEM POINTLARI (oldindan ogohlantirish)

| Muammo | Yechim |
|---|---|
| E-auksion JS yuklanishi sekin | `wait_until="networkidle"` + `wait_for_selector` |
| Cyrillic vs Latin variantlar | `unidecode` + lowercase + manual map |
| INN'da leading zero yo'qoladi | `str.zfill(9)` har joyda |
| Geo-koordinata yo'q | Nominatim geocoding fallback |
| Lot olib tashlangan/o'chirilgan | try/except + log + skip |
| Captcha | recaptcha bor (bosh sahifada), lekin lot-view'da yo'q — tekshiring |
| IP block | proxy rotation, yoki sleep oshirish |
| Sahifa formati o'zgargan | selektorlarni regularno qayta tekshiring |

---

## 4. KEYINGI BOSQICH (siz tugatgandan keyin)

ML model trening uchun:
- **Unsupervised:** Isolation Forest + DBSCAN narx anomaliyasi uchun
- **Supervised:** XGBoost (200 yorliqdan) + cross-validation
- **Graph:** NetworkX + community detection (Louvain) affiliated firmalarni topish uchun
- **Embedding:** Lot tavsifini Claude API'ga yuborib semantic red-flag aniqlash

Lekin bu **2-bosqich**. Avval dataset.

---

## 5. RESURSLAR

- Sitemap: https://e-auksion.uz/sitemap_index.xml
- Lot misol: https://e-auksion.uz/lot-view?lot_id=23469523
- Playwright Python docs: https://playwright.dev/python/
- Embedding model: https://huggingface.co/intfloat/multilingual-e5-small
- pandas-profiling: https://github.com/ydataai/ydata-profiling
- Nominatim: https://nominatim.org/

---

## 6. DEADLINE

**24 soat** boshlanish vaqtidan.

**Status update'lar:**
- Soat 4: Qadam 1-2 tugagan, selektorlar `selectors.md` da
- Soat 8: Qadam 3 tugagan, 10K lot scrape qilingan
- Soat 14: Qadam 4-5 tugagan, features tayyor
- Soat 20: Qadam 6-7 tugagan, EDA hisobot bor
- Soat 24: Hammasi `data/` papkasida, GitHub commit qilingan

---

## 7. SAVOL/MUAMMO BO'LSA

Slack/Telegram: [PM ismi]
Code review: PR oching, asosiy branch'ga merge qilmang
Stuck > 1 soat: To'xtang, yordam so'rang.

---

**Yutaylik!**
