"""AuksionWatch Telegram bot — fuqaro uchun tezkor tergov interfeysi.

Bizning FastAPI backend'ga ustqurma — saytga kirmasdan ham ishlatish mumkin.
Stateless: bot xotirada hech narsa saqlamaydi, har komanda backend'ga so'rov yuboradi.

Komandalar:
  /start          — salomlashish + komandalar ro'yxati
  /check <lot_id> — lot xavf tahlili (5 sek)
  /firma <hint>   — sotuvchi tarixi (davaktiv/court/bank)
  /report         — bugungi TOP 8 qizil bayroq
  /stats          — umumiy statistika + TOP 5 hudud
  /help           — yordam matni

Auto-lookup: agar foydalanuvchi shunchaki raqam yuborsa (12345678), avtomatik /check ishlaydi.
"""
import asyncio
import os
import sys
from pathlib import Path

import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

# .env faylidan BOT_TOKEN va boshqa env'larni yuklash (agar mavjud bo'lsa)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

# Konfiguratsiya — env yoki defaults
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000").strip()  # FastAPI backend manzili
WEB_BASE = os.getenv("WEB_BASE", "http://localhost:3000").strip()  # Frontend manzili (inline tugmalar uchun)

# Token yo'q bo'lsa — foydali xato xabari va chiqish
if not BOT_TOKEN:
    print("[bot] ERROR: BOT_TOKEN env var not set")
    print("    1. Telegram'da @BotFather ga kiring")
    print("    2. /newbot yuboring, ko'rsatmalarga amal qiling")
    print("    3. Token oling, bot/.env fayliga yozing:")
    print("       BOT_TOKEN=123456:abcdef...")
    sys.exit(1)


# ISO-style hudud kodlari → o'zbekcha nom (chat'da ko'rsatish uchun)
REGION_NAMES = {
    "UZ-TK": "Toshkent shahri",
    "UZ-TO": "Toshkent viloyati",
    "UZ-AN": "Andijon",
    "UZ-BU": "Buxoro",
    "UZ-FA": "Farg'ona",
    "UZ-JI": "Jizzax",
    "UZ-XO": "Xorazm",
    "UZ-NG": "Namangan",
    "UZ-NW": "Navoiy",
    "UZ-QA": "Qashqadaryo",
    "UZ-SA": "Samarqand",
    "UZ-SI": "Sirdaryo",
    "UZ-SU": "Surxondaryo",
    "UZ-QR": "Qoraqalpog'iston",
}


def fmt_uzs(v):
    """Pul miqdorini o'qib bo'lish formatga o'gir: 1230000 → '1.23 mln so''m'."""
    if v is None:
        return "—"
    if v >= 1e12:
        return f"{v/1e12:.2f} trln so'm"
    if v >= 1e9:
        return f"{v/1e9:.2f} mlrd so'm"
    if v >= 1e6:
        return f"{v/1e6:.2f} mln so'm"
    return f"{int(v):,} so'm".replace(",", " ")


def risk_emoji(level: str) -> str:
    """Risk darajasi → emoji (chat ko'rinishi)."""
    return {"high": "🚩", "medium": "⚠️", "low": "✅"}.get(level, "•")


def risk_label(level: str) -> str:
    """Risk darajasi → o'zbekcha matn."""
    return {"high": "YUQORI XAVF", "medium": "O'RTA XAVF", "low": "OZ XAVF"}.get(
        level, level.upper()
    )


WELCOME = (
    "🚩 <b>AuksionWatch</b>\n"
    "<i>E-AUKSION ochiq nazorat tizimi</i>\n\n"
    "Davlat mol-mulki auksionlaridagi shubhali sxemalarni AI yordamida "
    "aniqlovchi mustaqil monitoring tizimi.\n\n"
    "<b>Komandalar:</b>\n"
    "<code>/check &lt;lot_id&gt;</code> — lot xavf tahlili\n"
    "<code>/firma &lt;hint&gt;</code> — sotuvchi tarixi (masalan: <code>/firma davaktiv</code>)\n"
    "<code>/report</code> — bugungi top qizil bayroqlar\n"
    "<code>/stats</code> — umumiy statistika\n"
    "<code>/help</code> — yordam\n\n"
    "🔗 Web: " + WEB_BASE + "\n"
    "📊 API: " + API_BASE + "/docs"
)


bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


async def api_get(path: str):
    """Backend FastAPI'ga GET so'rov — JSON natija qaytaradi.

    Xato bo'lsa httpx exception ko'taradi (chaqiruvchi xandelaydi).
    """
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(f"{API_BASE}{path}")
        r.raise_for_status()
        return r.json()


def _is_public_url(u: str) -> bool:
    """Telegram inline tugmalar uchun URL public bo'lishi shart.

    localhost yoki 127.0.0.1 — ishlamaydi (Telegram serveri bunday URL'ni rad qiladi).
    Production'da Railway URL bo'lsa ✓, develop'da yo'q.
    """
    return u.startswith(("http://", "https://")) and "localhost" not in u and "127.0.0.1" not in u


def lot_keyboard(lot_id: int) -> InlineKeyboardMarkup:
    """Lot ostida ko'rsatiladigan inline tugmalar.

    Doim e-auksion manba linki bor (HTTPS).
    Web'da batafsil tugmasi faqat WEB_BASE public bo'lsa qo'shiladi.
    """
    rows = [
        [
            InlineKeyboardButton(
                text="📂 Manba (e-auksion)",
                url=f"https://e-auksion.uz/lot-view?lot_id={lot_id}",
            ),
        ]
    ]
    if _is_public_url(WEB_BASE):
        rows[0].insert(
            0,
            InlineKeyboardButton(
                text="🔍 Web'da batafsil",
                url=f"{WEB_BASE}/lot/{lot_id}",
            ),
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ───────── KOMANDA HANDLERLARI ─────────

@dp.message(CommandStart())
async def start(msg: Message):
    """/start — botni birinchi marta ishga tushirish, salomlashish."""
    await msg.answer(WELCOME, disable_web_page_preview=True)


@dp.message(Command("help"))
async def help_cmd(msg: Message):
    """/help — komandalar ro'yxatini qayta ko'rsatish."""
    await msg.answer(WELCOME, disable_web_page_preview=True)


@dp.message(Command("check"))
async def check(msg: Message, command: CommandObject):
    """/check <lot_id> — bitta lot uchun risk hisobotini chiqarish.

    Backend'dan /api/lots/{id} chaqirib, flag'lar va AI xulosani ko'rsatadi.
    Inline tugmalar: e-auksion manba + Web'da batafsil.
    """
    arg = (command.args or "").strip()
    # Argument bo'sh yoki raqam emas — yordam ko'rsatish
    if not arg or not arg.lstrip("#").isdigit():
        await msg.answer(
            "❓ Lot raqamini kiriting:\n<code>/check 90000000</code>"
        )
        return
    lot_id = int(arg.lstrip("#"))
    try:
        data = await api_get(f"/api/lots/{lot_id}")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            await msg.answer(f"❌ Lot #{lot_id} bizning bazada topilmadi.")
            return
        raise
    except Exception as e:
        await msg.answer(f"❌ Backend xatosi: {e}")
        return

    lot = data["lot"]
    flags = lot.get("flags") or []

    region = REGION_NAMES.get(lot.get("region"), lot.get("region") or "—")
    auction = "🔒 YOPIQ" if lot.get("auction_type") == "closed" else "Ochiq"

    text = (
        f"{risk_emoji(lot['risk_level'])} <b>{risk_label(lot['risk_level'])}</b> · "
        f"<code>{int(lot['risk_score'])}/100</code>\n\n"
        f"<b>Lot #{lot['id']}</b>\n"
        f"<i>{lot.get('title') or lot.get('lot_type') or 'Nomsiz'}</i>\n\n"
        f"📍 <b>Hudud:</b> {region}\n"
        f"💰 <b>Boshlang'ich:</b> {fmt_uzs(lot.get('start_price'))}\n"
        f"🎯 <b>Sotuv:</b> {fmt_uzs(lot.get('sold_price'))}\n"
        f"⚖️ <b>Auksion:</b> {auction}\n"
        f"👥 <b>Ishtirokchilar:</b> {lot.get('bidders_count') or '—'}\n"
    )

    if flags:
        text += f"\n🚩 <b>Aniqlangan signallar ({len(flags)}):</b>\n"
        for f in flags:
            text += f"  • {f['title']} <code>+{f['score']}</code>\n"

    if lot.get("ai_summary"):
        text += f"\n💡 <b>AI xulosa:</b>\n<i>{lot['ai_summary']}</i>"

    await msg.answer(text, reply_markup=lot_keyboard(lot["id"]))


@dp.message(Command("firma"))
async def firma(msg: Message, command: CommandObject):
    """/firma <hint> — sotuvchi tarixi va statistikasi.

    hint = davaktiv / court / bank / individual.
    Backend'dan /api/firms/{hint} chaqiradi va TOP 5 xavfli lotni ko'rsatadi.
    """
    arg = (command.args or "").strip().lower()
    if not arg:
        await msg.answer(
            "❓ Sotuvchi turi kiriting:\n"
            "<code>/firma davaktiv</code>\n"
            "<code>/firma court</code>\n"
            "<code>/firma bank</code>"
        )
        return
    try:
        data = await api_get(f"/api/firms/{arg}")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            await msg.answer(f"❌ '{arg}' sotuvchisi bizning bazada topilmadi.")
            return
        raise
    except Exception as e:
        await msg.answer(f"❌ Backend xatosi: {e}")
        return

    text = (
        f"🏛 <b>Sotuvchi:</b> <code>{data['seller_hint']}</code>\n\n"
        f"📊 <b>Statistika:</b>\n"
        f"  • Jami lotlar: <b>{data['total_lots']}</b>\n"
        f"  • Yopiq auksion: <b>{data['closed_pct']:.1f}%</b>\n"
        f"  • Yuqori xavfli: <b>{data['high_risk_count']}</b>\n\n"
        f"🚩 <b>Eng xavfli lotlari:</b>\n"
    )
    for i, lot in enumerate(data["items"][:5], 1):
        emoji = risk_emoji(lot["risk_level"])
        text += (
            f"{i}. {emoji} <b>#{lot['id']}</b> — "
            f"<code>{int(lot['risk_score'])}</code> · {fmt_uzs(lot.get('start_price'))}\n"
        )

    kb = None
    if _is_public_url(WEB_BASE):
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔍 Web'da to'liq tarix",
                        url=f"{WEB_BASE}/lots?seller_hint={arg}",
                    )
                ]
            ]
        )
    await msg.answer(text, reply_markup=kb)


@dp.message(Command("report"))
async def report(msg: Message):
    """/report — bugungi TOP 8 qizil bayroq + umumiy statistika."""
    try:
        data = await api_get("/api/red-flags/today?limit=8")
        stats = await api_get("/api/stats")
    except Exception as e:
        await msg.answer(f"❌ Backend xatosi: {e}")
        return

    items = data.get("items", [])
    text = (
        f"📰 <b>Bugungi qizil bayroqlar hisoboti</b>\n\n"
        f"📊 Jami bazada: <b>{stats['total']}</b> lot\n"
        f"🚩 Yuqori xavfli: <b>{stats['high_risk']}</b> ({fmt_uzs(stats['high_risk_value_uzs'])})\n"
        f"🔒 Yopiq auksion: <b>{stats['closed_auctions']}</b>\n\n"
        f"<b>TOP {len(items)} eng xavfli lot:</b>\n\n"
    )
    for i, lot in enumerate(items, 1):
        region = REGION_NAMES.get(lot.get("region"), lot.get("region") or "—")
        text += (
            f"<b>{i}.</b> {risk_emoji(lot['risk_level'])} "
            f"<code>#{lot['id']}</code> · <code>{int(lot['risk_score'])}/100</code>\n"
            f"   📍 {region} · {fmt_uzs(lot.get('start_price'))}\n"
            f"   <i>{(lot.get('title') or '—')[:80]}</i>\n\n"
        )

    kb = None
    if _is_public_url(WEB_BASE):
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🌐 Web dashboard", url=f"{WEB_BASE}/"),
                    InlineKeyboardButton(text="🗺 Xarita", url=f"{WEB_BASE}/map"),
                ]
            ]
        )
    await msg.answer(text, reply_markup=kb)


@dp.message(Command("stats"))
async def stats_cmd(msg: Message):
    """/stats — umumiy raqamlar (jami lot, high/medium, qiymat) + TOP 5 xavfli hudud."""
    try:
        s = await api_get("/api/stats")
    except Exception as e:
        await msg.answer(f"❌ Backend xatosi: {e}")
        return
    top_regions = sorted(
        s.get("high_risk_by_region", []),
        key=lambda r: -r["high_count"],
    )[:5]
    text = (
        f"📊 <b>AuksionWatch statistikasi</b>\n\n"
        f"📁 Jami lotlar: <b>{s['total']}</b>\n"
        f"🚩 Yuqori xavf: <b>{s['high_risk']}</b>\n"
        f"⚠️ O'rta xavf: <b>{s['medium_risk']}</b>\n"
        f"🔒 Yopiq auksionlar: <b>{s['closed_auctions']}</b>\n"
        f"💰 Jami qiymat: <b>{fmt_uzs(s['total_value_uzs'])}</b>\n"
        f"⚡ Xavfli qiymat: <b>{fmt_uzs(s['high_risk_value_uzs'])}</b>\n\n"
    )
    if top_regions:
        text += "<b>TOP 5 xavfli hudud:</b>\n"
        for i, r in enumerate(top_regions, 1):
            name = REGION_NAMES.get(r["region"], r["region"])
            text += f"{i}. {name}: <b>{r['high_count']}</b> 🚩\n"
    await msg.answer(text)


@dp.message(F.text.regexp(r"^\d{6,}$"))
async def auto_lookup(msg: Message):
    """Auto-lookup: foydalanuvchi shunchaki raqam yuborsa avtomatik /check ishlatadi.

    Misol: 90000000 → /check 90000000.
    UX'ni soddalashtirish uchun (foydalanuvchi 'check' yozishini eslab o'tirmaydi).
    """
    fake_command = CommandObject(prefix="/", command="check", args=msg.text)
    await check(msg, fake_command)


async def main():
    """Botni ishga tushirish — long polling rejimida."""
    print(f"[bot] starting AuksionWatch bot")
    print(f"[bot] API base: {API_BASE}")
    print(f"[bot] Web base: {WEB_BASE}")
    me = await bot.get_me()
    print(f"[bot] @{me.username} ({me.first_name})")
    # drop_pending_updates=True — restart vaqtida yig'ilib qolgan eski update'larni tashlaydi
    await dp.start_polling(bot, drop_pending_updates=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[bot] stopped")
