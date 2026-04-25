# e-auksion.uz DOM Selectorlari

**Tekshirilgan lot:** https://e-auksion.uz/lot-view?lot_id=23469523  
**Tekshirilgan sana:** [skript ishlatilganda to'ldiring]  
**Playwright versiyasi:** 1.44

---

## MUHIM: Vue SPA haqida

Sahifa `<div id="q-app">` bilan keladi — barcha kontent JavaScript tomonidan render qilinadi.
Har doim `wait_for_selector` dan keyin o'qing:

```python
await page.wait_for_selector(".lot-number, [class*='lot-title']", timeout=15000)
```

---

## Selectorlar jadvali

| Maydon | CSS Selector | Misol qiymat | Izoh |
|--------|-------------|--------------|------|
| `lot_number` | `.lot-number, [class*='lot-id']` | "№23469523" | `text_content()` |
| `lot_type` | `.lot-type, [class*='property-type']` | "yer uchastkasi" | `text_content()` |
| `region` | `.lot-region, [class*='region']` | "Toshkent shahri" | `text_content()` |
| `district` | `.lot-district, [class*='district']` | "Yunusobod tumani" | `text_content()` |
| `address` | `.lot-address, [class*='address']` | "Amir Temur ko'chasi" | `text_content()` |
| `area_m2` | `.lot-area, [class*='area']` | "1500 m²" | raqamni parse qiling |
| `start_price` | `.start-price, [class*='start-price']` | "250 000 000 so'm" | raqamni parse qiling |
| `current_price` | `.current-price, [class*='current-price']` | "280 000 000 so'm" | raqamni parse qiling |
| `auction_type` | `.auction-type, [class*='auction-type']` | "ochiq" / "yopiq" | `text_content()` |
| `bidders_count` | `.bidders-count, [class*='participants']` | "3" | raqamni parse qiling |
| `seller_name` | `.seller-name, [class*='seller'] .name` | "Davaktiv" | `text_content()` |
| `seller_inn` | `.seller-inn, [class*='seller'] .inn` | "201234567" | 9 raqam |
| `start_time` | `.auction-start, [class*='start-date']` | "2026-04-20 10:00" | datetime parse |
| `end_time` | `.auction-end, [class*='end-date']` | "2026-04-25 18:00" | datetime parse |
| `status` | `.lot-status, [class*='status']` | "tugagan" | `text_content()` |
| `winner_inn` | `.winner-inn, [class*='winner'] .inn` | "987654321" | 9 raqam, bo'lmasligi mumkin |
| `description` | `.lot-description, [class*='description']` | "..." | `inner_text()` |
| `geo_lat` | `[class*='map'] [data-lat], script[type*='json']` | "41.31" | JSON yoki data-attr |
| `geo_lon` | `[class*='map'] [data-lon], script[type*='json']` | "69.27" | JSON yoki data-attr |
| `images` | `.lot-images img, [class*='gallery'] img` | ["url1", "url2"] | `src` atributlari |
| `documents` | `a[href*='.pdf'], [class*='documents'] a` | ["pdf_url1"] | `href` atributlari |

---

## Fallback strategiyasi

Agar selector ishlamasa:
1. `raw_html` ni saqlang — keyinchalik BeautifulSoup bilan parse qilish mumkin
2. `page.evaluate()` bilan JavaScript'dan ma'lumot olish:
   ```python
   data = await page.evaluate("() => window.__INITIAL_STATE__ || window.__nuxt__")
   ```
3. Network request'larni tutib olish (`page.route` yoki `page.on("response")`)

---

## Tekshirish buyruqlari

```bash
# Brauzerda selector'ni tekshirish (DevTools Console):
document.querySelector('.lot-number')?.textContent
document.querySelectorAll('.lot-images img').length

# Playwright'da tekshirish:
python scripts/test_selectors.py
```

---

## O'zgarishlar tarixi

| Sana | Nima o'zgardi | Kim o'zgartirdi |
|------|---------------|-----------------|
| [to'ldiring] | Dastlabki selectorlar | ML Engineer |
