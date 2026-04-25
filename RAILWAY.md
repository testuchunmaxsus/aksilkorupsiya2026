# 🚂 Railway deployment guide

AuksionWatch — 3 ta service'ni Railway'ga deploy qilish.

```
┌─────────────────────────────────────────────────────────┐
│  Railway Project: auksionwatch                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  backend     │  │  frontend    │  │  bot         │  │
│  │  (FastAPI)   │  │  (Next.js)   │  │  (Telegram)  │  │
│  │  port 8000   │  │  port 3000   │  │  polling     │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                  │                  │         │
│         ▼                  │                  │         │
│   /data Volume       ──────┘ NEXT_PUBLIC_     ▼         │
│   (SQLite + JSON)            API_URL          API_BASE  │
└─────────────────────────────────────────────────────────┘
```

---

## 1. Prerequisites

- Railway hisob: https://railway.com
- GitHub repo'ga push qilingan: `https://github.com/testuchunmaxsus/aksilkorupsiya2026`
- Telegram bot token (@BotFather'dan)

---

## 2. Backend service (FastAPI) — RECOMMENDED with Postgres

### A) Postgres-aware deploy (recommended)

#### Step 1 — Add Postgres
```
Railway → + New → Database → Add PostgreSQL
└── This creates a Postgres service and exposes DATABASE_URL automatically.
```

#### Step 2 — Deploy backend
```
+ New → GitHub repo → auksilkorupsiya2026
└── Settings → Root Directory: leave empty (uses /backend/Dockerfile via railway.json)
└── Variables → Reference: DATABASE_URL (linked from Postgres service)
```

Railway auto-injects `DATABASE_URL` (format `postgres://user:pass@host:port/db`).
The backend code rewrites it to `postgresql+psycopg2://...` automatically — no manual change needed.

#### Environment variables
| Variable | Qiymat | Tavsif |
|---|---|---|
| `DATABASE_URL` | (auto from Postgres ref) | postgres://... — backend normalizes |
| `ALLOWED_ORIGINS` | `https://auksionwatch.up.railway.app` | Frontend domain(s), comma-separated |
| `AUTOSEED` | `1` | Birinchi bo'sh DB'ga lots_parsed.json import qiladi (~10K lot, ~1 daqiqa) |
| `PORT` | (Railway auto) | HTTP port |

#### Healthcheck
Settings → Health Check Path: `/healthz` (Dockerfile'da ham bor)

#### Domain
Settings → Networking → Generate Domain → `auksionwatch-api.up.railway.app`

---

### B) SQLite + Volume (oddiy, lekin scaling cheklovi)

Bitta replica uchun yaroqli. Ko'p replica bo'lsa Postgres'ga o'ting.

```
Settings → Volumes → New Volume
  Name: data
  Mount Path: /app/data
  Size: 2 GB
```
Variables: `DATABASE_URL = sqlite:////app/data/auksionwatch.db`

---

## 3. Frontend service (Next.js)

### Yaratish
```
Railway → + New → GitHub repo → same repo
└── Settings → Root Directory: frontend
└── Build: Docker (auto-detects frontend/Dockerfile)
```

### Environment variables
| Variable | Qiymat | Tavsif |
|---|---|---|
| `PORT` | `3000` (Railway sets) | HTTP port |
| `NEXT_PUBLIC_API_URL` | `https://auksionwatch-api.up.railway.app` | Backend domain |
| `NODE_ENV` | `production` | (auto) |

### Build args
Settings → Build → Build Args:
```
NEXT_PUBLIC_API_URL=https://auksionwatch-api.up.railway.app
```

### Domain
Settings → Networking → Generate Domain → `auksionwatch.up.railway.app`

---

## 4. Telegram bot service

### Yaratish
```
Railway → + New → GitHub repo → same repo
└── Settings → Root Directory: bot
└── Build: Docker (auto-detects bot/Dockerfile)
```

### Environment variables
| Variable | Qiymat | Tavsif |
|---|---|---|
| `BOT_TOKEN` | `123456:ABCDEF...` | @BotFather'dan |
| `API_BASE` | `https://auksionwatch-api.up.railway.app` | Backend domain |
| `WEB_BASE` | `https://auksionwatch.up.railway.app` | Frontend domain (inline tugmalar uchun) |

> ⚠️ **Token rotation:** demo'da chiqib qolgan tokenni @BotFather → /mybots → Revoke qilib, yangi tokenni Railway env'ga yozing.

---

## 5. Deployment ketma-ketligi

```bash
# 1. Push o'zgarishlarni
cd D:\hackaton\auksionwatch
git add .
git commit -m "Railway deployment config"
git push

# 2. Backend service'ni yarating (yuqoridagi 2-bo'lim)
#    + Volume + DATABASE_URL + healthcheck
#    Wait → first boot will auto-seed from lots_parsed.json (~30s)

# 3. Backend domain'ni nusxa qiling, e.g.:
#    https://auksionwatch-api.up.railway.app

# 4. Frontend service'ni yarating (3-bo'lim)
#    NEXT_PUBLIC_API_URL = backend domain
#    Build → wait

# 5. Frontend domain'ni nusxa qiling, e.g.:
#    https://auksionwatch.up.railway.app

# 6. Backend ALLOWED_ORIGINS env'ga frontend domain qo'shing
#    Restart backend

# 7. Bot service yarating (4-bo'lim)
#    BOT_TOKEN, API_BASE, WEB_BASE — 3 env
#    Bot polling avtomatik boshlanadi
```

---

## 6. Tekshiruv (post-deploy)

```bash
# Backend
curl https://auksionwatch-api.up.railway.app/healthz
# → {"status":"ok"}

curl https://auksionwatch-api.up.railway.app/api/stats
# → {"total": 11204, ...}

# Frontend
open https://auksionwatch.up.railway.app

# Bot — Telegramda
/start
/check 23446154
```

---

## 7. Custom domain (ixtiyoriy)

Frontend uchun:
1. Settings → Networking → Custom Domain → `auksionwatch.uz`
2. DNS provider'da CNAME yoki A record qo'shing (Railway ko'rsatadi)
3. SSL avtomatik (Let's Encrypt)

Backend uchun: subdomain ishlatish tavsiya qilinadi `api.auksionwatch.uz`.

---

## 8. Monitoring

Railway dashboard:
- **Metrics** — CPU, RAM, Network
- **Deployments** — har push'dan keyin avtomatik deploy
- **Logs** — real-time stdout/stderr (filter qilinadi)
- **Database** — agar Postgres'ga o'tsangiz: Railway Postgres add-on

---

## 9. Postgres'ga migratsiya (optional, scaling uchun)

Railway Postgres add-on:
```
+ New → Database → PostgreSQL
└── Variables → DATABASE_URL avtomatik backend service'ga ulanadi
```

`DATABASE_URL` avtomatik `postgresql://...` formatda — backend kod uni qabul qiladi (SQLModel + SQLAlchemy).

Migratsiya:
```bash
# Local DB'ni dump
sqlite3 data/auksionwatch.db .dump > /tmp/dump.sql

# Postgres-compatible'ga aylantirish va import (qo'lda yoki pgloader)
# Yoki: backend AUTOSEED=1 bilan qayta seed
```

---

## 10. Cost estimate

Railway free tier: $5 trial, keyin $5/oy "Hobby plan".

| Service | RAM | CPU | Disk | $/oy |
|---|---|---|---|---|
| Backend | 512 MB | 0.5 vCPU | 2 GB volume | ~$5 |
| Frontend | 512 MB | 0.5 vCPU | — | ~$5 |
| Bot | 256 MB | 0.25 vCPU | — | ~$3 |
| **Jami** | | | | **~$13/oy** |

Hobby plan ($5/oy includes ~$5 usage) — 3 service uchun ~$10-15/oy.

---

## 11. Xato hollarda

| Xato | Yechim |
|---|---|
| Backend boshlanmaydi | Logs → tekshiring; `data/lots_parsed.json` mavjudmi? |
| Frontend 502 | `NEXT_PUBLIC_API_URL` to'g'ri sozlanganmi? Build args qo'shilganmi? |
| Bot polling fail | `BOT_TOKEN` to'g'rimi? @BotFather'dan revoke qilib qayta oldingizmi? |
| CORS error | Backend `ALLOWED_ORIGINS` ga frontend domainni qo'shing |
| DB ma'lumot yo'q | `AUTOSEED=1` env va volume'da `lots_parsed.json` |

---

## 12. Production checklist

- [ ] Bot token ROTATSIYA qilingan (suhbatdagi token bekor)
- [ ] `ALLOWED_ORIGINS` aniq domain'lar (`*` emas)
- [ ] Custom domain SSL bilan
- [ ] Backend volume backup
- [ ] Logs monitoring (Sentry yoki Logtail)
- [ ] Rate limit (Cloudflare yoki FastAPI middleware)
- [ ] Postgres'ga migratsiya (>50K lot uchun)
