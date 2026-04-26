"""E-auksion API JSON'ni bizning Lot modeliga moslash.

api_scraper.py'dan kelgan boy JSON'ni AuksionWatch ichki schema'ga aylantiradi:
  - region_name → UZ-XX kod
  - is_closed: 1 → auction_type='closed'
  - baholangan_narx → appraised_price (real benchmark!)
  - c_user.name → seller_name
  - is_descending_auction → is_descending (teskari auksion flagi)

Playwright'dan ko'ra boy ma'lumot — geo koordinata, ishtirokchilar soni,
hujjatlar ro'yxati, MIB (sud ijrochisi) ma'lumoti.
"""
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent.parent

# Region ID → ISO kod (api regions_id maydonidan)
REGION_MAP = {
    1: "UZ-TK",   # Toshkent shahri
    2: "UZ-TO",   # Toshkent viloyati
    3: "UZ-AN",   # Andijon
    4: "UZ-BU",   # Buxoro
    5: "UZ-FA",   # Farg'ona
    6: "UZ-JI",   # Jizzax
    7: "UZ-XO",   # Xorazm
    8: "UZ-NG",   # Namangan
    9: "UZ-NW",   # Navoiy
    10: "UZ-QA",  # Qashqadaryo
    11: "UZ-BU",  # (some APIs use 11 for Buxoro)
    12: "UZ-SA",  # Samarqand
    13: "UZ-SI",  # Sirdaryo
    14: "UZ-SU",  # Surxondaryo
    15: "UZ-QR",  # Qoraqalpog'iston
}

REGION_NAME_TO_CODE = {
    "Toshkent shahri": "UZ-TK",
    "Toshkent viloyati": "UZ-TO",
    "Andijon viloyati": "UZ-AN",
    "Buxoro viloyati": "UZ-BU",
    "Farg`ona viloyati": "UZ-FA",
    "Farg'ona viloyati": "UZ-FA",
    "Jizzax viloyati": "UZ-JI",
    "Xorazm viloyati": "UZ-XO",
    "Namangan viloyati": "UZ-NG",
    "Navoiy viloyati": "UZ-NW",
    "Qashqadaryo viloyati": "UZ-QA",
    "Samarqand viloyati": "UZ-SA",
    "Sirdaryo viloyati": "UZ-SI",
    "Surxondaryo viloyati": "UZ-SU",
    "Qoraqalpog`iston Respublikasi": "UZ-QR",
    "Qoraqalpog'iston Respublikasi": "UZ-QR",
}


def localized(field: Any, lang: str = "uz") -> str | None:
    """Multilanguage maydondan to'g'ri tilni tanlash.

    e-auksion API ko'p maydonlarni 4 tilda beradi: name_uz/ru/uk/en.
    Bizga uz birinchi, keyin ru fallback.
    """
    if not field:
        return None
    if isinstance(field, str):
        return field
    if isinstance(field, dict):
        for k in (f"name_{lang}", "name_uz", "name_ru", "name_en"):
            if field.get(k):
                return field[k]
    return None


def parse_lot(raw: dict) -> dict | None:
    """Raw API JSON'ni Lot model schema'siga moslash.

    Returns None agar lot xato yoki bo'sh bo'lsa.
    """
    # Xato yoki bo'sh javob — None qaytaramiz, pipeline davom etadi
    if not raw or "error" in raw or not raw.get("id"):
        return None

    # ── Identifikator va joylashuv ──
    lot_id = raw["id"]
    region_name = localized(raw.get("region_name"))
    region_code = REGION_NAME_TO_CODE.get(region_name) or REGION_MAP.get(raw.get("regions_id"))
    district = localized(raw.get("area_name"))
    address = raw.get("joylashgan_manzil")
    # Geo-koordinata — xarita uchun (string sifatida keladi, float'ga o'giramiz)
    lat = float(raw["lat"]) if raw.get("lat") else None
    lng = float(raw["lng"]) if raw.get("lng") else None

    # ── Auksion turi va faollik ──
    # is_closed=1 → yopiq auksion (Fazekas CRI eng kuchli signali)
    auction_type = "closed" if raw.get("is_closed") == 1 else "open"
    bidders_count = raw.get("auction_cnt")  # ishtirokchilar soni
    views = raw.get("view_count")           # lotni necha marta ko'rilgan

    # ── Narxlar ──
    start_price = raw.get("start_price")
    # current_price — agar auksion tugagan bo'lsa, sotuv narxi
    sold_price = raw.get("current_price") if raw.get("current_price") and raw["current_price"] > 0 else None
    appraised = raw.get("baholangan_narx")  # rasmiy baholangan narx — REAL benchmark
    deposit = raw.get("zaklad_summa")        # zakalat puli
    step_summa = raw.get("step_summa")       # auksion qadami

    # ── Sotuvchi ma'lumotlari ──
    c_user = raw.get("c_user") or {}
    seller_name = c_user.get("name") or raw.get("user_fio")
    seller_phone = c_user.get("phone") or raw.get("user_phone")
    seller_address = c_user.get("full_address")
    seller_id = raw.get("c_users_id")  # numeric ID — graf tahlili uchun

    # ── MIB (sud ijrochisi) ma'lumotlari ──
    # Sud orqali sotilayotgan mol-mulk uchun (executive officer / pristav)
    mib_inn = raw.get("mib_inn")
    mib_name = raw.get("mib_name")
    mib_executor = raw.get("mib_executor_fio")

    # ── Sotuvchi turini aniqlash (heuristika) ──
    # MUHIM: e-auksion.uz da uch xil mol-mulk sotiladi:
    #   1) Davaktiv — DAVLAT mol-mulki (Davlat aktivlarini boshqarish agentligi)
    #   2) MIB / sud — qarzdorlardan musodara qilingan SHAXSIY mol-mulk
    #   3) Yuridik shaxs / bankrot biznes
    # Default'ni "davaktiv" qilish noto'g'ri edi — auksionning katta qismi MIB
    # orqali shaxsiy mol-mulk. Default endi "unknown".
    if mib_name or raw.get("is_from_mib_portal") == 1:
        seller_hint = "court"               # sud ijrochilari xizmati orqali
    elif raw.get("is_davaktiv") == 1 or (raw.get("source") == "davaktiv"):
        seller_hint = "davaktiv"            # rasmiy davlat aktivlari
    else:
        seller_hint = "unknown"             # aniqlanmadi — ko'r-ko'rona "davlat" demaymiz

    # ── Lot turi va auksion uslubi ──
    lot_type = localized(raw.get("confiscant_categories_name"))   # batafsil kategoriya
    lot_type_group = localized(raw.get("confiscant_groups_name")) # umumiy guruh
    auction_method = localized(raw.get("auction_type_name"))      # "Auksion" / "Tanlov"
    auction_style = localized(raw.get("lot_types_name"))          # "Oshirib borish"

    title = raw.get("name")
    status = localized(raw.get("lot_statuses_name"))
    start_time = raw.get("start_time_str") or raw.get("start_time")
    end_time = raw.get("order_end_time_str")

    # Hujjatlar va rasmlar (count'i ko'rsatamiz, full URL keyin)
    docs = [d.get("file_name") for d in (raw.get("confiscant_documents_list") or []) if d]
    images = [
        i.get("document_resources_id") for i in (raw.get("confiscant_images_list") or []) if i
    ]

    # Bo'lib to'lash (favoritism belgisi)
    is_term = raw.get("is_term_payment") == 1
    term_months = raw.get("term_month")

    return {
        "lot_id": lot_id,
        "url": raw.get("_url") or f"https://e-auksion.uz/lot-view?lot_id={lot_id}",
        "title": title,
        "lot_type": lot_type,
        "lot_type_specific": lot_type_group,
        "address": address,
        "region": region_code,
        "district": district,
        "geo_lat": lat,
        "geo_lon": lng,
        "start_price": start_price,
        "sold_price": sold_price,
        "appraised_price": appraised,
        "deposit": deposit,
        "step_price": step_summa,
        "installment_months": term_months if is_term else None,
        "auction_method": auction_method,
        "auction_style": auction_style,
        "auction_type": auction_type,
        "start_time": start_time,
        "deadline": None,
        "end_time": end_time,
        "status": status,
        "views": views,
        "bidders_count": bidders_count,
        "seller_hint": seller_hint,
        "seller_name": seller_name,
        "seller_id": seller_id,
        "seller_phone": seller_phone,
        "seller_address": seller_address,
        "mib_inn": mib_inn,
        "mib_name": mib_name,
        "mib_executor": mib_executor,
        "documents_count": len(docs),
        "images_count": len(images),
        "is_descending": raw.get("is_descending_auction") == 1,
        "is_juridical_only": raw.get("is_juridical_can_apply") == 0
        and raw.get("is_physical_can_apply") == 0,
    }


def main():
    """CLI — lots_api.json (raw) → lots_parsed.json (structured)."""
    raw_path = ROOT / "data" / "lots_api.json"
    out_path = ROOT / "data" / "lots_parsed.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8"))

    parsed = []
    fail = 0
    for r in raw:
        try:
            p = parse_lot(r)
            if p:
                parsed.append(p)
            else:
                fail += 1
        except Exception as e:
            fail += 1
            print(f"[parse] error lot {r.get('lot_id')}: {e}")

    out_path.write_text(json.dumps(parsed, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[parse] {len(parsed)} parsed / {fail} failed -> {out_path}")

    # quick stats
    has_geo = sum(1 for p in parsed if p.get("geo_lat"))
    has_appraised = sum(1 for p in parsed if p.get("appraised_price"))
    closed = sum(1 for p in parsed if p.get("auction_type") == "closed")
    multi_bid = sum(1 for p in parsed if (p.get("bidders_count") or 0) > 1)
    descending = sum(1 for p in parsed if p.get("is_descending"))
    print(f"  has geo coords: {has_geo}")
    print(f"  has appraised price: {has_appraised}")
    print(f"  closed auctions: {closed}")
    print(f"  multi-bidder: {multi_bid}")
    print(f"  descending auction: {descending}")


if __name__ == "__main__":
    main()
