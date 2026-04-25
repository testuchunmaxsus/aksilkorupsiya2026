# AuksionWatch — Pitch matni (to'liq)

> 4 xil davomiylikdagi pitch + demo skripti + Q&A tayyorgarlik. Hammasi tayyor — faqat **mashq qiling**.

**Loyiha:** AuksionWatch — E-AUKSION ochiq nazorat tizimi
**Live demo:** https://aksilkorrupsiya2026.up.railway.app
**Repo:** https://github.com/testuchunmaxsus/aksilkorupsiya2026

---

## ⏱️ 1 DAQIQALIK PITCH (Lift Pitch · 60s)

> "2026-yanvar. Akmalxon Ortiqov — Davlat aktivlari boshqarish agentligi rahbari hibsga olindi. 250 mlrd so'mlik yer **yopiq auksionda 120 mlrd** ga sotilgan. Davlat 130 mlrd so'm zarar ko'rdi.
>
> Bu izolyatsiyalangan emas — yiliga **4.2 trln so'm** korrupsiya zarari (Prezident bayonoti).
>
> **AuksionWatch** — civic AI: e-auksion.uz dagi 23M+ lotni xalqaro standartlar (OECD, Fazekas, FATF) asosida tahlil qiladi. **18+ rule + XGBoost ensemble (CV AUC 0.98) + 9266 ta Fargʻona loti**.
>
> Production live: **aksilkorrupsiya2026.up.railway.app**. 11,204 lot tahlilda, 6,784 yuqori xavfli aniqlangan, 186 ML-KRITIK.
>
> Ukraine ProZorro $6 mlrd, Brazil ALICE EUR 35M+ saqladi. **Biz ham shu yo'lda**, lekin O'zbekiston voqeligiga moslashtirilgan."

**Maqsad:** 60 soniyada hakam telefonini ochib URL'ga kirsin.

---

## ⏱️ 3 DAQIQALIK PITCH (Demo Day · 180s)

### [0:00–0:25] HOOK + Muammo
> "Hammasi 130 mlrd so'mdan boshlandi.
>
> 2026-yanvarda Davlat aktivlari boshqarish agentligi rahbari hibsga olindi. Sxema oddiy: 250 mlrd so'mlik yer **yopiq** auksionga chiqarilib, **bitta** ishtirokchi bilan 120 mlrd ga sotildi. Davlat zarari — 130 mlrd so'm.
>
> Va bu — mingdan biri. OECD bahosiga ko'ra, davlat loyihalari qiymatining 20–30% i korrupsiyaga yo'qoladi. O'zbekistonda yiliga e-auksion'da 19.7 trln so'm aylanadi."

### [0:25–0:55] Bo'shliq
> "Hozir nima bor? Davlat ichki AI quryapti — e-anticor.uz, lekin **fuqaro ko'rmaydi**, jurnalist foydalana olmaydi. data.egov.uz portali rasman bor — lekin **bo'sh**, e-auksion ma'lumoti yo'q. Tergov jurnalist 1 ta firmani 2 hafta qo'lda tekshiradi.
>
> Bo'shliq aniq: **fuqaro uchun ochiq, AI bilan kuchaytirilgan monitoring tizim yo'q**."

### [0:55–1:55] Yechim + mini-demo
> "AuksionWatch shu bo'shliqni to'ldiradi. (URL ko'rsatish: aksilkorrupsiya2026.up.railway.app)
>
> 3 qatlamli AI:
> 1. **Rule engine** — OECD/Fazekas standartlari, 18+ rule. Har signal ostida formula, ma'lumot maydoni va xalqaro manba.
> 2. **ML ensemble** — XGBoost (CV AUC 0.98) + IsolationForest. 33 feature, weak-supervised. Rule'lar ko'r joyda ML topadi.
> 3. **PEP layer** — FATF Recommendation 12 bo'yicha mansabdor screening.
>
> (Lot ochish: /lot/23439577)
>
> Mana real misol: bu lot — bizning **rule engine 35/100** (low) baholaydi, lekin **ML 92/100 KRITIK** chiqaradi. Sabab: 'bankruptcy + chegirmasiz + 35 marta qayta e'lon'. ML rule'lar topa olmaydigan sxemani ushladi.
>
> Ma'lumot manbasi: e-auksion.uz ochiq sitemap (23M+ lot ID public) + rasmiy Excel hisobotlari. Hozir DB'da 11,204 lot, 6,784 yuqori xavfli aniqlangan."

### [1:55–2:30] Bozor + biznes model
> "4 ta daromad oqimi: davlat kontraktlar (Aksilkorrupsiya agentligi audit asbob), donor grantlar (UNDP, USAID, EU — Ukraine ProZorro $5M+ olgan), media/NGO subscription (Kun.uz, Gazeta.uz, CABAR), korxona compliance check.
>
> Halqaro tajriba bizni tasdiqlaydi: **Ukraine ProZorro $6 mlrd, Brazil ALICE EUR 35M+/yil, Czech zIndex −5% xarajat saqladi.**"

### [2:30–3:00] Holat + so'rov
> "Hozir: production live, 12 sahifa frontend, Telegram bot, public API + CSV/JSON eksport, GitHub'da CC BY-SA 4.0 litsenziyasi bilan.
>
> Bizga **$50K seed grant**, OpenSanctions API kreditlari, davlat hamkorlik (NDA), va OCCRP/CABAR mentor kerak.
>
> AuksionWatch — Ukraine ProZorro+DOZORRO ekvivalentining O'zbekistonga moslashtirilgan civic versiyasi. **Har bir auksion ochiq nazoratda bo'lsin.**"

---

## ⏱️ 5 DAQIQALIK PITCH (Investor · 300s)

### Slide 1 → 2 — HOOK [0:00–0:30]
> "Hozir taqdimotda mening eng kichik raqamim — 130. Eng kattasi — 4.2 trillion. Birinchisi — Ortikhov keysidagi davlat zarari million so'mda. Ikkinchisi — Prezident bayonotidagi yillik korrupsiya hajmi.
>
> 130 milliard so'mlik yer **120 ga sotildi**. Yopiq auksion. Bitta ishtirokchi. Mansabdor sherikligi. 2026-yanvar."

### Slide 3 → 4 — Solution + Market [0:30–1:30]
> "AuksionWatch shu sxemalarni **avval** topishga qaratilgan. Bizning AI 3 qatlamga ega:
>
> Birinchi qatlam — **rule engine**. 18+ rule, har biri OECD, Fazekas Cambridge tadqiqoti yoki World Bank IACRC standartiga asoslangan. Har lot uchun risk score 0-100. Eng muhimi: har signal ortida formula bor, qaysi maydondan kelganligi ko'rinadi va manba linki bosib o'tiladi. Bu — 'qora quti' emas.
>
> Ikkinchi qatlam — **ML ensemble**. XGBoost classifier va IsolationForest anomaly detection. Trening: weak-supervised, 114 yorliq Fargʻona viloyatidan. CV AUC 0.98. 33 feature. Rule engine ko'r joyda ML topadi: bankruptcy + no-discount, takroriy auksion + monopol kombinatsiyalari.
>
> Uchinchi qatlam — **PEP screening** FATF Recommendation 12 bo'yicha. Mansabdor ismi yoki familiyasi bilan fuzzy match. Hozircha 3 ta ochiq mansabdor (Ortikhov, Murodov, Turdimov), production'da OpenSanctions API bilan 200K+.
>
> Bozor: 4 segment. Davlat kontraktlar (Aksilkorrupsiya agentligi), donor grantlar (UNDP, USAID, EU — Ukraine ProZorro $5M+ olgan), media subscription, korxona compliance."

### Slide 5 → 7 — Differentiator + Status [1:30–3:00]
> "Bizning farq aniq: e-anticor.uz davlat ichki tizimi, fuqaro ko'rmaydi. data.egov.uz rasman bor — lekin bo'sh. Hech kim bizning ishni qilmagan.
>
> Holat: 8 soatlik hackathon ichida MVP yaratdik. Hozir production live: **aksilkorrupsiya2026.up.railway.app**. Backend FastAPI Postgres'da. Frontend Next.js. Telegram bot. ML pipeline 9264 Fargʻona lotini scoring qildi — 186 KRITIK, 788 YUQORI. Ma'lumot Railway Postgres'da, 11,204 lot. CC BY-SA 4.0 ochiq litsenziyasi bilan.
>
> Real misol — sizga ko'rsataman. (Lot detail ochiladi)
>
> Lot raqami 23439577. Bizning rule engine 35/100 — low risk. Lekin ML 92/100 KRITIK. Nega? Bu lot bankruptcy ostida, chegirmasiz, 35 marta qayta auksionga chiqarilgan. ML training data'sida bu pattern juda shubhali — XGBoost 98% ehtimol bilan red flag chiqaradi. Bizning rule'larda alohida 'bankruptcy combo' yo'q edi — ML qoplaydi.
>
> Side-by-side panel ham bor — har lot uchun rule va ML score yonma-yon, divergence bo'lsa avtomatik tushuntirish chiqadi."

### Slide 11 → 10 — Halqaro precedent + ask [3:00–4:30]
> "Bu metodologiya yangi emas. Mihály Fazekas Cambridge'da Single Bidder Indicator'ni 2015-yilda tasdiqladi — Transparency International CPI bilan korrelatsiyasi 0.71. OECD Anti-Corruption Outlook 2026 bunga 5 toifa taksonomiya berdi.
>
> Davlatlar tajribasi gapiradi:
> - Ukraine ProZorro + DOZORRO civic AI — 2014-dan boshlab **$6 mlrd** saqladi.
> - Brazil ALICE — Federal Audit Court AI — 2020-yilda **EUR 35M+** zarar oldi.
> - Czech zIndex — hokimliklar shaffoflik reytingi — yuqori reytingli organlar **5% kam** to'laydi.
> - Slovakia 2011 Open Tender qonuni — 2-3% narx tushdi.
>
> AuksionWatch shu yo'lda. **Ukrainaning DOZORRO modeli + Brazilning ALICE risk-detection + Slovakning ochiqlik printsipi** — O'zbekiston voqeligiga moslashtirilgan.
>
> Bizga keyingi bosqich uchun kerak:
> 1. **$50K seed grant** — server, OpenSanctions API kreditlari, ish haqi
> 2. **Davlat hamkorlik** — Aksilkorrupsiya agentligi bilan rasmiy NDA
> 3. **Halqaro mentor** — OCCRP yoki CABAR Asia
> 4. **Mediya hamkor** — Kun.uz yoki Spot.uz pilot tergov
>
> 2026-Q3 da 100K lot. 2027 da iOS/Android. 2027+ da OCDS Cardinal hamkorligi."

### Slide 12 — Yopilish [4:30–5:00]
> "Bir savol qoldi: nima uchun davlat o'zi qilmaydi?
>
> Davlat ichki tool quryapti. Lekin Mihály Fazekas formulasi bo'yicha shaffoflik faqat **fuqarolik nazorat layeri** bilan ishlaydi. Ukraine'da DOZORRO — bu davlat tizimining JAMOAVIY pari, davlat raqibi emas.
>
> AuksionWatch ham xuddi shunday. Davlat e-anticor'ni qursin — biz fuqaro layer'ni qurib turibmiz. Birgalikda — **har bir auksion ochiq nazoratda bo'lsin**.
>
> Rahmat. Savollar?"

---

## ⏱️ 10 DAQIQALIK PITCH — DEMO BILAN

5 daqiqalik pitch + 5 daqiqalik **live demo** (8 qadam, har biri ~30 sek).

### Demo qadamlar

#### 1. Bosh sahifa
**URL:** `https://aksilkorrupsiya2026.up.railway.app/`

> "Mana bizning panel. 11,204 lot DB'da, 6,784 yuqori xavfli, 1 trillion so'mga yaqin xavfli qiymat. Vaqt grafigi — auksion dinamikasi. Pastda hududlar bo'yicha taqsimot."

#### 2. Lotlar reestri
**URL:** `/lots?risk_level=high`

> "200 ta yuqori xavfli lot. Filter, qidiruv, sort. Bir bosishda CSV/JSON eksport — jurnalist butun datasetni 1 sekundda oladi."

#### 3. Lot batafsil — RULE vs ML divergence
**URL:** `/lot/23439577`

> "Mana eng qiziq misol. Bu lotning **rule engine score'i — 35**, low risk. **ML score — 92**, KRITIK. Side-by-side panel ko'rinmoqda. Pastda divergence tushuntirishi: 'ML rule'lar qoplay olmaydigan murakkab pattern (bankruptcy + chegirmasiz) topdi'.
>
> Pastga qarang — har red flag ostida formula, qaysi maydondan kelganligi va xalqaro manba linki bor. Hech kim 'qaerdan oldingiz?' deya olmaydi."

#### 4. Sotuvchilar reytingi
**URL:** `/sellers`

> "Top sotuvchilar reytingi. Niyozov Quvonchbek — 3,755 lot, 99.1% xavfli. Bu Fargʻonadagi 9266 lotning 40.8% i. Top 3 sotuvchi 81% lotni nazorat qiladi — EU klassifikatsiyasi bo'yicha bu **state capture** belgisi."

#### 5. PEP signal'lari
**URL:** `/pep`

> "FATF R12 bo'yicha mansabdor screening. Hozircha demo'da 3 ta ochiq keys: Ortikhov hibsda, Murodov yangi rahbar, Turdimov sobiq hokim. Production'da OpenSanctions API bilan 200K+ global PEP."

#### 6. Tarmoq grafi
**URL:** `/network`

> "Sotuvchilar va hududlar interaktiv tarmog'i. Niyozov atrofidagi katta qizil tugun — Fargʻona viloyati 40% nazorat. Bu Fazekas 'state capture' tahlili bilan to'liq mos."

#### 7. Methodology
**URL:** `/methodology`

> "Hammasi ochiq: 5 OECD/OCP toifa, 18+ rule, har birining ostida vazn, formula, xalqaro manba. 8 ta akademik manba — OECD, Fazekas Cambridge, World Bank IACRC, OCDS Cardinal, FATF R12."

#### 8. Telegram bot — TELEFON BILAN ⭐ (eng kuchli lahza)
**Bot:** `@AuksionWatch_bot`

> "Saytga kirmasdan ham ishlatish mumkin. Telefonimni ko'taring. Yozaman: `/check 23439577`. (5 sek kutiladi). Mana — bot 5 sekundda risk hisoboti, sabab matni, e-auksion manba linkini berdi.
>
> **Hakamlar, sizlar ham hozir telefoningizda sinab ko'ring** — har bir o'zbek fuqarosi har qanday lotni 5 sekundda tekshira oladi."

#### 9. PDF eksport — yopilish
> "Va eng oxiri — har lot uchun PDF tergov hisoboti. (Lot detail'da 'HISOBOT (PDF)' tugma bosiladi). Bir bosishda jurnalist sud uchun ham, gazeta uchun ham hujjatlangan dalil oladi."

---

## 🎯 KEY MESSAGES (har joyda takrorlang)

1. **"Har bir auksion ochiq nazoratda bo'lsin"** — slogan, oxirida aytasiz
2. **"$6 mlrd Ukraine'da, EUR 35M Brazil'da — biz ham shu yo'lda"** — halqaro tasdiq
3. **"Davlat raqibi emas — fuqarolik layer"** — pozitsiya, agressiv emas
4. **"OECD, Fazekas, FATF — uydirma emas, ilm bor"** — credibility
5. **"Production live, hozir ishlatasiz"** — proof, vaporware emas

---

## ❓ Q&A — KUTILGAN SAVOLLAR

### Texnik

**Q: Ma'lumot rasmiymi? E-auksion'dan qonuniy oldingizmi?**
> 100% rasmiy va qonuniy. Asosiy manba — e-auksion.uz public sitemap (23M+ lot ID ochiq, robots.txt ruxsat berilgan) + rasmiy Excel hisobotlari (Davaktiv chiqaradigan). Har lot detail'da manba linki — har kim tasdiqlay oladi.

**Q: 8 soatda 11K lot tahlilini qanday qildingiz?**
> Aniq vaqt taqsimoti: 1 soat infra, 2 soat scraper (Playwright + httpx, e-auksion'ning yashirin API'si /api/front/lot-info topildi), 3 soat backend + risk engine, 2 soat frontend. ML chimiz parallelda 24 soatda Excel pipeline + XGBoost training qildi.

**Q: ML model kichik (114 yorliq) — bu ishonchlimi?**
> Bu **MVP bosqichi** — biz weak-supervised yorliqlash bilan boshladik. CV AUC 0.98 — Fargʻona doirasida juda yaxshi, lekin biz biladigan: kelgusi versiyada 1000+ qo'lda yorliqlangan dataset kerak. Rule engine bilan birga ishlatish — gibrid approach Fazekas tadqiqotida tavsiya qilingan.

**Q: Soxta alarm bo'lsa-chi (false positive)?**
> Risk score 0-100 — 'qonuniy ayb' degani emas, faqat 'tekshirish uchun ko'rsatma'. Har lot detail'da disclaimer bor. UI'dagi til neytral: 'flagged', 'shubhali signal', 'manba linki'. Foydalanuvchi o'zi xulosa chiqaradi.

**Q: Bizdan yashirinish mumkinmi (adversarial)?**
> Soxta raqobatchi yaratish, threshold splitting kabi 12 ta strategiyani `chetel/13_Threat_model_evasion.md` hujjatda batafsil tahlil qildik. Hozirgi v1.2 da coverage 35%. v2'da NetworkX graf community detection bilan 75% ga oshadi. Bitta signal aylanib o'tilishi mumkin, **5 toifa bir vaqtda** — yo'q.

### Biznes

**Q: Davlat sizni yopib qo'ymaydimi?**
> Biz faqat **ochiq ma'lumot** ishlatamiz — e-auksion sitemap, rasmiy Excel hisobotlari. Hech qanday yopiq DB hack qilmaymiz. CC BY-SA 4.0 — har kim foydalanishi mumkin. Davlat raqibi emasmiz, e-anticor.uz ichki AI bilan bir xil maqsadda — fuqarolik layer.

**Q: Daromad qachon keladi?**
> 6 oydan keyin — pilot grant (UNDP yoki Soros) realistik. 1 yil ichida B2B subscription (Kun.uz, Gazeta.uz). 2 yil ichida davlat kontrakt (e-anticor.uz bilan integratsiya). Ukraine ProZorro 5 yilda $6 mlrd saqlash isboti — long-term ROI raqamli.

**Q: Nega bu xukumat o'zi qilmagan?**
> Davlat e-anticor.uz ni 2026-mart'dan launch qilyapti — lekin **ichki tizim**. Fuqarolik nazorat layer'i hech qaysi davlatda hukumat tomonidan qurilmaydi (interest conflict). Ukraine'da DOZORRO ham NGO (Transparency International). Biz shu modelni takrorlaymiz.

### Strategik

**Q: Sizning haqiqiy raqobatchi kim?**
> Texnik raqobatchi yo'q — bizning ishni hech kim qilmagan. Tabiiy raqobatchilar: davlat e-anticor.uz (ichki, 2026-mart launch) va texnologiyalashmagan tergov jurnalistlari. Bizning afzallik: **realdan tezroq** + **ochiq**.

**Q: 5 yildan keyin?**
> 3 senariy:
> 1. **Eng yaxshi:** O'zbekiston Slovakiya 2011 yo'lidan ketadi — barcha shartnomalar majburiy ochiq, AuksionWatch standart asbob bo'ladi.
> 2. **O'rta:** Davlat va biz parallel ishlaymiz, fuqarolar har ikkalasini ishlatadi.
> 3. **Eng yomon:** Davlat bizni cheklaydi (qonun bilan), lekin litsenziyamiz CC BY-SA 4.0 — Tor mirror, GitHub backup, halqaro hosting bor.

**Q: Eng katta xavf nima?**
> 3 ta xavf:
> 1. **Legal challenge** — defamation da'vosi. Yengish: faqat ochiq ma'lumot, neytral til, manba link.
> 2. **Government takedown** — yopib qo'yish. Yengish: multi-region (Vercel + Hetzner), Tor mirror, IPFS.
> 3. **Adversarial evasion** — koruptsioner aylanib o'tadi. Yengish: 8 qatlamli defense in depth.

---

## 🎬 PRESENTATION TIPS

### Tayyorgarlik
- **Computer'ni o'chiring**, qog'ozda reja tuzing (qoidaga ko'ra)
- **Hikoya yarating:** Intro (Ortikhov) → Problem (4.2 trln) → Struggle (hech kim qilmaydi) → Happy End (AuksionWatch)
- **3 marta repetitsiya** qiling — vaqtni o'lchang
- Telegram bot tayyor turibsin (`/check 23439577` ekran ko'rsatishga tayyor)
- Internet uzilsa zaxira: PDF screenshots tayyorlang

### Demo paytida
- **Brauzer ochiq** Railway URL bilan
- Zoom 125% — hakam orqadan o'tirsa ham ko'rinadi
- **Click konkret** — har 30 sek bir sahifa o'zgaradi
- Telefon ekran kabel orqali proyektorga (yoki ekran almashish)

### Til
- **Qisqa jumla** — 12 so'zdan oshmasin
- Raqamlar o'rta darajada — "bir necha milliard" emas, "130 mlrd"
- "Innovatsion", "noyob", "analogi yo'q" — **ishlatmang** (qoidaga ko'ra)
- "Biz qildikku" emas — **"Mana, ishlayapti"** ko'rsating

### Tana tili
- Ko'zga qarab gapiring (har hakamga ~10 sek)
- Telefon yoki kompyuterga emas — auditoriyaga
- Qo'l harakatlari ochiq, kaftlar ko'rinadi
- Slaydlarga orqa qilmang — yon turing

---

## 📋 OXIRGI CHECKLIST (pitch'dan 30 daq oldin)

- [ ] Backend live: `curl https://aksilkorupsiya2026-production.up.railway.app/healthz`
- [ ] Frontend live: brauzerda ochiq, Ctrl+Shift+R
- [ ] Telegram bot — `/start` test
- [ ] Demo lot ochiq tab'da: `/lot/23439577`
- [ ] PDF print test — bir marta sinab ko'ring
- [ ] Pitch slaydlari yuklangan (PDF backup ham)
- [ ] Telefon zaryad to'liq
- [ ] Suv stakan
- [ ] Hujjat papka — pitch.pptx, demo skripti, fact sheet

---

## 🎤 OXIRGI JUMLA — har holatda aytasiz

> **"Har bir auksion ochiq nazoratda bo'lsin. Rahmat."**

---

## 📞 KONTAKT (slayd 12 da)

- **Live demo:** https://aksilkorrupsiya2026.up.railway.app
- **GitHub:** https://github.com/testuchunmaxsus/aksilkorupsiya2026
- **Telegram bot:** @AuksionWatch_bot
- **Email:** geminiuchunmaxsus@gmail.com

---

**Versiya:** v1.2 — 2026-04-25 · **Litsenziya:** CC BY-SA 4.0
