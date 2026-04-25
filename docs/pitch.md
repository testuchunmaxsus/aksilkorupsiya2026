---
marp: true
theme: gaia
class: invert
paginate: true
backgroundColor: '#0a0a0a'
color: '#fafafa'
style: |
  section { font-family: 'Segoe UI', sans-serif; }
  h1 { color: #ef4444; }
  h2 { color: #f87171; }
  strong { color: #fca5a5; }
  .accent { color: #ef4444; font-weight: bold; }
  .small { font-size: 0.7em; color: #a1a1aa; }
---

# 🚩 AuksionWatch
## E-AUKSION ochiq nazorat tizimi

**Aksilkorrupsiya hackathon 2026**
Jamoa: [Sizning jamoangiz]

<span class="small">Ma'lumot manbasi: e-auksion.uz · Litsenziya: CC BY-SA 4.0</span>

---

# Muammo: 130 mlrd so'mlik sxema

**2026-yanvar:** Akmalxon Ortiqov (Davaktiv) hibsga olindi.

| Holat | Qiymat |
|---|---|
| Yer haqiqiy bahosi | **250 mlrd so'm** |
| **Yopiq auksionda** sotildi | 120 mlrd so'm |
| Davlat zarari | **130 mlrd so'm** |

> "53 trln so'm o'zlashtirish, 4.2 trln so'm korrupsiya zarari aniqlandi."
> — Sh. Mirziyoyev, 2026-yanvar

---

# Bo'shliq

| Mavjud | Yo'q |
|---|---|
| 23M+ lot ma'lumotlari | Public API |
| `/open-data` sahifa | Ma'lumot yo'q (sahifa BO'SH) |
| Hukumat ichki AI (e-anticor.uz) | Fuqaroga ochiq AI vosita |
| Skandal post-factum | Real-vaqt aniqlash |

**Hukumat ichki AI quryapti — biz fuqaro uchun ochiq AI quramiz.**

---

# Yechim: AuksionWatch

**E-auksion.uz dagi 23M+ lotni AI yordamida tahlil qilib, korrupsiya sxemalarini OLDINDAN aniqlovchi ochiq monitoring tizimi.**

3 ta foydalanuvchi:
- 📰 **Jurnalist** — 30 soniyada tergov
- 📢 **Aktivist / NGO** — xaritada qizil bayroqlar
- 👤 **Fuqaro** — sotib olishdan oldin tekshirish

---

# Demo

## 6 ta avtomatik signal:
1. 🔒 **Yopiq auksion** (+30)
2. 👤 **1 ishtirokchi** (+25)
3. 💰 **Past boshlang'ich narx** (median'dan -60%) (+20)
4. 📉 **Chuqur diskont** (sotuv -30%+) (+20)
5. 📅 **Uzoq muddatli to'lov** (+8)
6. 🚫 **Past ko'rishlar** (+7)

→ **Risk score 0-100** + xaritada qizil/sariq/yashil

---

# Texnologiya stack

| Qatlam | Texnologiya |
|---|---|
| Scraper | Playwright + Python (Vue SPA, sitemap public) |
| Backend | FastAPI + SQLite + SQLModel |
| Frontend | Next.js 16 + Tailwind + Leaflet + OpenStreetMap |
| Telegram | aiogram 3 — 5 ta komanda, stateless API klient |
| AI/Risk | Rules-based + (kelgusi: ML model + Claude API) |
| Deploy | Railway + Vercel |

**MVP statistikasi (8 soatlik hackathon):**
- 300 ta real lot scrape qilindi
- 14 ta viloyat
- 20 ta yuqori xavfli lot aniqlandi
- Web + Telegram bot + public REST API = 3 ta interfeys

---

# Naf raqamlarda

| Ko'rsatkich | Hozir | AuksionWatch bilan |
|---|---|---|
| Skandal aniqlash | Oylar (post-factum) | Soatlar (oldindan) |
| 1 lot tergov | 2 hafta jurnalist | 30 soniya |
| Yopiq auksion shaffofligi | 0% | 100% |
| Public API | Yo'q | Bor |

**1 ta sxema to'xtatilsa = 100+ mlrd so'm xalq pulini saqlash.**

---

# Keyingi qadam

1. ML model (XGBoost + 200 yorliqli ground-truth)
2. Claude API integratsiyasi (lot tavsifini AI tahlil)
3. Telegram bot (push-alert obunalar)
4. Affiliated firma graf tahlili (NetworkX)
5. Boshqa platformalar bilan integratsiya:
   - xarid.uzex.uz, openbudget.uz, decisions.esud.uz
6. Aksilkorrupsiya agentligi bilan rasmiy hamkorlik

---

# Rahmat!

## 🚩 AuksionWatch
**Har bir auksion ochiq nazoratda bo'lsin.**

GitHub: github.com/[jamoa]/auksionwatch
Demo: [URL]

<span class="small">Litsenziya: CC BY-SA 4.0 · Ma'lumot manbasi: e-auksion.uz</span>
