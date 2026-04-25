# 🚩 AuksionWatch

> **E-AUKSION antikorrupsiya monitoring tizimi**
> Davlat mol-mulki auksionlaridagi shubhali sxemalarni AI yordamida aniqlovchi ochiq monitoring tizimi.

**Aksilkorrupsiya hackathon 2026 MVP** — 8 soatlik dasturchi vaqti.

---

## Tarkib

```
auksionwatch/
├── backend/        # FastAPI + SQLite + risk scoring engine
│   ├── main.py     # REST API endpointlari
│   ├── models.py   # SQLModel jadval ta'riflari
│   ├── db.py       # DB engine + session
│   ├── risk.py     # 6 ta red-flag rule
│   └── ingest.py   # JSON → DB pipeline
├── frontend/       # Next.js 16 + Tailwind + Leaflet
│   ├── app/        # Sahifalar (bosh, /lots, /map, /lot/[id])
│   ├── components/ # RiskBadge, LotMap, StatCard, NavBar
│   └── lib/api.ts  # API klient
├── scraper/        # Playwright + sitemap parser
│   ├── sitemap.py  # 23M+ lot ID public sitemap'dan
│   ├── scrape.py   # Vue SPA Playwright headless
│   └── parser.py   # Text → structured fields
├── bot/            # Telegram bot (aiogram 3)
│   ├── main.py     # 5 ta komanda: /check, /firma, /report, /stats, /help
│   └── .env        # BOT_TOKEN (siz qo'shasiz)
├── data/           # SQLite DB + scraped JSON
└── docs/           # TZ, pitch deck, demo skripti
```

---

## Tezkor ishga tushirish

### Talablar
- Python 3.10+
- Node.js 20+
- 2 GB disk

### 1. Backend
```bash
cd auksionwatch
pip install -r requirements.txt
python -m playwright install chromium
```

### 2. Ma'lumot yig'ish
```bash
# 1000 lot ID sitemap'dan
python scraper/sitemap.py --limit 1000

# 300 ta lotni Playwright bilan scrape qilish (~5 daqiqa)
python scraper/scrape.py --limit 300 --concurrency 6

# Strukturali maydonlarga parse
python scraper/parser.py

# DB'ga ingest + risk scoring + demo lotlar
python -m backend.ingest
```

### 3. Backend ishga tushirish
```bash
uvicorn backend.main:app --reload --port 8000
```
- Swagger: http://localhost:8000/docs
- API: http://localhost:8000/api/stats

### 4. Frontend
```bash
cd frontend
npm install
npm run dev
```
http://localhost:3000

### 5. Telegram bot (ixtiyoriy)
```bash
cd bot
cp .env.example .env
# .env ichida BOT_TOKEN ni @BotFather dan olib qo'ying
python main.py
```
Komandalar: `/check <lot_id>`, `/firma <hint>`, `/report`, `/stats`, `/help`

---

## Asosiy xususiyatlar

### 1. Real-vaqt scraping
- e-auksion.uz **public sitemap**'dan 23M+ lot ID
- Playwright headless Chromium bilan har bir lot sahifasi
- 4-6 concurrent page = ~50 lot/daqiqa

### 2. Risk scoring engine (6 ta rule)
| Rule | Score | Tushuntirish |
|---|---|---|
| `closed_auction` | +30 | Yopiq auksion |
| `single_bidder` | +25 | 1 ishtirokchi |
| `underpriced` | +20 | Hudud medianidan -60% past |
| `deep_discount` | +20 | Sotuv narxi -30%+ past |
| `seller_closed_pattern` | +15 | Sotuvchining 50%+ lotlari yopiq |
| `long_installment` | +8 | 60+ oy bo'lib to'lash |
| `low_visibility` | +7 | <10 ko'rish + yopiq |

**Risk level:** `<40 low`, `40-69 medium`, `≥70 high`

### 3. Public REST API
- `GET /api/stats` — umumiy statistika
- `GET /api/lots` — filtrli ro'yxat
- `GET /api/lots/{id}` — batafsil + sotuvchi tarixi
- `GET /api/red-flags/today` — bugungi top 10
- `GET /api/map/markers` — xarita uchun marker'lar
- `GET /api/firms/{seller_hint}` — firma tarixi

### 4. Dashboard
- 🏠 **Bosh sahifa:** statistika + bugungi qizil bayroqlar
- 🗺️ **Xarita:** Leaflet + OpenStreetMap, rang risk darajasiga qarab
- 📋 **Lotlar:** filtr, qidiruv, pagination
- 🔍 **Lot batafsil:** AI tahlil + red flag bloki + sotuvchi tarixi + manba link

### 5. Telegram bot
- `/check <lot_id>` — lot xavf tahlili (5 sekundda javob, inline Web tugma bilan)
- `/firma <hint>` — sotuvchi statistikasi va eng xavfli lotlari
- `/report` — bugungi TOP qizil bayroqlar
- `/stats` — umumiy statistika + TOP 5 hudud
- Auto-lookup: faqat raqam yuborilsa avtomatik `/check` ishlaydi

---

## Texnologiya stack

| Qatlam | Texnologiya |
|---|---|
| Scraper | Python 3.14, Playwright 1.49, httpx, tenacity |
| Backend | FastAPI 0.118, SQLModel 0.0.22, SQLite |
| Frontend | Next.js 16, React 19, Tailwind 4, Leaflet, Recharts |
| AI/Risk | Rules-based (kelgusi: XGBoost + Claude API) |

---

## MVP statistikasi (8 soatlik hackathon)

- ✅ 300 ta real lot scrape qilindi
- ✅ 14 ta viloyat
- ✅ 6 ta risk-flag turi
- ✅ 20 ta yuqori xavfli lot aniqlandi
- ✅ 1+ trln so'm xavfli lot qiymati
- ✅ 5 ta REST API endpoint
- ✅ 4 ta sahifa (bosh, xarita, lotlar, batafsil)

---

## Litsenziya

**CC BY-SA 4.0**

Ma'lumot manbasi: [e-auksion.uz](https://e-auksion.uz) (ochiq sitemap)

Loyiha hech qanday rasmiy davlat organi bilan bog'liq emas. Biz faqat ochiq ma'lumotlardan foydalanamiz va jamoatchilik nazoratini ta'minlashga qaratilganmiz.

---

## Hujjatlar

- [Texnik topshiriq (TZ)](../TZ_AuksionWatch.md)
- [ML Engineer vazifasi](../ML_VAZIFA_dataset.md)
- [Pitch deck (Marp)](docs/pitch.md)
- [Demo skripti](docs/demo_script.md)

---

## Jamoa

**[Jamoangiz nomi]**
- Backend & Scraper
- Frontend & UI
- ML Engineer (parallel)
- Designer & Pitcher

---

**Har bir auksion ochiq nazoratda bo'lsin.** 🚩
