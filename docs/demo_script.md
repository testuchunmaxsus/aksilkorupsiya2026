# DEMO SKRIPTI — AuksionWatch (90 soniya)

## Kontekst (15s)
> "Hammasi 2026-yanvardan boshlandi. Akmalxon Ortiqov — Davlat aktivlarini boshqarish agentligi rahbari hibsga olindi. **130 mlrd so'mlik yer yopiq auksionda yo'qoldi.** Bu kabi sxemalarni biz AVVAL ushlash uchun AuksionWatch'ni yaratdik."

## Bosh sahifa (15s)
**Brauzerda oching:** http://localhost:3000

> "Mana bizning panel. Real e-auksion.uz dan 300 ta lot scrape qildik — siz hozir aslida e-auksion'da bor lotlarning ma'lumotini ko'ryapsiz. **20 ta yuqori xavfli lot aniqladik. Umumiy qiymati 1 trillion so'mdan ortiq.**"

(Stats kartochkalarni ko'rsatish)

## Xarita (20s)
**Bosing:** "Xaritani ko'rish"

> "Mana O'zbekiston bo'yicha barcha lotlar. Qizil — yuqori xavf, sariq — o'rta, yashil — normal. **Toshkentdagi qizil nuqtaga bosing.** Mana popup: 'Lot #X, YUQORI XAVF, 87 ball'. 'Batafsil' tugmasiga bosamiz."

## Lot batafsil (25s)
> "**AI tahlil bloki:** 'YUQORI XAVF: Yopiq auksion, 1 ishtirokchi, past narx. Bu lot Ortiqov-stilidagi sxemaga juda o'xshash.'

**O'ng paneldagi 'Aniqlangan belgilar' bloki:**
- 🔒 Yopiq auksion +30
- 👤 1 ishtirokchi +25
- 💰 Past boshlang'ich narx +20
- 📉 50% diskont +20

**Manba linkini bosish:** 'Eng asosiysi — bu yerda yozilgan har bir narsani siz e-auksion.uz da o'zingiz tasdiqlab ko'rishingiz mumkin. Ochiq ma'lumot, ochiq nazorat.'"

## Sotuvchi tarixi (10s)
> "**Pastdagi 'Sotuvchining boshqa lotlari' bloki**: bu sotuvchining oldingi 5 ta lotini ko'rasiz — qancha qizil bayroqli? Hammasi! Demak — sxema."

## Telegram bot (15s) — wow lahzasi
**Telefonni ko'taring, hakamlarga ko'rsating:**

> "Saytga kirmasdan ham foydalanish mumkin. Mana — bizning Telegram bot."

(Telefonda yozing: `/check 90000000`)

> "5 sekundda javob: 100/100 risk, 6 ta signal, AI xulosa, manba linki. **Hakamlar, sizlar ham telefoningizda ushbu botni sinab ko'rishingiz mumkin.** Bu — har bir o'zbek fuqarosi har qanday lotni 5 sekundda tekshira olishi degani."

## Yopilish (5s)
> "Bu MVP. **8 soatda yasadik. 300 ta lot bilan ishlaydi. 23 millionga osongina kengaytiriladi.** Backend, AI, xarita, Telegram bot, public API — hammasi GitHub'da ochiq, CC BY-SA 4.0 litsenziyasi bilan.

**Har bir auksion ochiq nazoratda bo'lsin.** Rahmat."

---

# Q&A — kutilgan savollar

**Q: Bu rasmiy ma'lumotmi yoki taxmin?**
A: Hammasi e-auksion.uz dan ochiq sitemap orqali olingan. Har bir lotda manba linki bor.

**Q: Nega davlat o'zi qila olmaydi?**
A: Quryapti — 2026-mart'dan e-anticor.uz launch bo'ladi. Lekin u **ichki tizim**, fuqaro ko'ra olmaydi. Bizniki — ochiq, jamoatchilik nazorat uchun.

**Q: Soxta alarm bo'lsa-chi?**
A: Risk score 0-100 — har bir signal ochiq tushuntirilgan. Foydalanuvchi nima sababdan flag qo'yilganini ko'radi va o'zi xulosa chiqaradi. Biz "ayblamaymiz" — biz "diqqat qiling" deb signal beramiz.

**Q: Geo-koordinata aniq emas?**
A: To'g'ri, MVP'da viloyat markaziga jitter qilinmoqda. Keyingi versiyada manzillarni Nominatim bilan to'liq geocode qilamiz.

**Q: Real ML modelmi?**
A: Hozircha rules-based — chunki 200+ yorliq kerak. Datasetimiz tayyor, ML chimiz parallel ishlamoqda. 2-bosqichda XGBoost + Claude API qo'shiladi.

**Q: Telegram bot bormi?**
A: Yo'q, hozircha. Lekin REST API ochiq — har kim bot yaratishi mumkin.

**Q: Litsenziya?**
A: CC BY-SA 4.0. To'liq ochiq. Davlat ham, NGO ham, jurnalist ham bepul foydalanishi mumkin.
