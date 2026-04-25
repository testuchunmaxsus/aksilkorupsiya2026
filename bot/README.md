# AuksionWatch Telegram bot

Mavjud FastAPI'ning Telegram interfeysi. 5 ta komanda:

| Komanda | Tavsif | Misol |
|---|---|---|
| `/start`, `/help` | Salomlashish + komandalar ro'yxati | — |
| `/check <lot_id>` | Lot xavf tahlili (flags + AI xulosa) | `/check 90000000` |
| `/firma <hint>` | Sotuvchi tarixi va statistikasi | `/firma davaktiv` |
| `/report` | Bugungi TOP qizil bayroqlar | — |
| `/stats` | Umumiy statistika + TOP hududlar | — |

**Qo'shimcha:** Faqat raqam yuborilsa (masalan `90000000`) — avtomatik `/check` ishlaydi.

## Ishga tushirish

### 1. Bot token oling
1. Telegramda [@BotFather](https://t.me/BotFather) ga kiring
2. `/newbot` yuboring, ko'rsatmalarga amal qiling
3. Tokenni nusxalang (formati: `123456789:ABC-DEF...`)

### 2. .env yarating
```bash
cd bot
cp .env.example .env
# .env ichida BOT_TOKEN=... ni yozing
```

### 3. Backend ishga tushirilgan bo'lsin
```bash
# alohida terminalda
cd auksionwatch
uvicorn backend.main:app --port 8000
```

### 4. Bot ishga tushiring
```bash
cd bot
python main.py
```

Konsolda:
```
[bot] starting AuksionWatch bot
[bot] @YourBotUsername (AuksionWatch)
```

Endi botingizda har qanday komandani sinab ko'ring.

## Demo skript (15 sekundlik bo'lim)

Hakam oldida:
1. Brauzerda dashboard ochilgan
2. Telefon ko'taring
3. Botda yozing: `/check 90000000`
4. 3 sekundda javob kelishini ko'rsating
5. Aytadigan jumla:
   > "Saytga kirmasdan ham har bir o'zbek fuqarosi 5 sekundda har qanday lotni tekshira oladi."

## Texnologiya
- aiogram 3.27 (async Python Telegram framework)
- httpx (FastAPI'ga so'rov)
- python-dotenv (.env'dan token)

Hech qanday qo'shimcha DB yoki sessiya kerak emas — bot stateless, har bir komanda mavjud REST API'ni chaqiradi.
