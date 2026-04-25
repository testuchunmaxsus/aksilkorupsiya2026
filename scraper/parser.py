"""Parse raw lot text into structured fields."""
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent.parent

REGIONS = {
    "Qoraqalpog`iston": "UZ-QR", "Qoraqalpog'iston": "UZ-QR", "Каракалпакстан": "UZ-QR",
    "Toshkent shahri": "UZ-TK", "Toshkent shahar": "UZ-TK",
    "Toshkent viloyati": "UZ-TO", "Toshkent vil": "UZ-TO",
    "Andijon": "UZ-AN", "Andijan": "UZ-AN",
    "Buxoro": "UZ-BU", "Bukhara": "UZ-BU",
    "Farg`ona": "UZ-FA", "Farg'ona": "UZ-FA", "Fergana": "UZ-FA",
    "Jizzax": "UZ-JI",
    "Xorazm": "UZ-XO", "Khorezm": "UZ-XO",
    "Namangan": "UZ-NG",
    "Navoiy": "UZ-NW",
    "Qashqadaryo": "UZ-QA",
    "Samarqand": "UZ-SA", "Samarkand": "UZ-SA",
    "Sirdaryo": "UZ-SI",
    "Surxondaryo": "UZ-SU",
}


def num(s: str) -> float | None:
    if not s:
        return None
    s = s.replace(" ", " ").replace(",", ".")
    s = re.sub(r"[^\d.]", "", s)
    try:
        return float(s) if s else None
    except ValueError:
        return None


def find(pattern: str, text: str, group: int = 1, flags=re.IGNORECASE | re.DOTALL) -> str | None:
    m = re.search(pattern, text, flags)
    return m.group(group).strip() if m else None


def detect_region(addr: str | None) -> tuple[str | None, str | None]:
    if not addr:
        return None, None
    region_code = None
    for key, code in REGIONS.items():
        if key.lower() in addr.lower():
            region_code = code
            break
    # district extraction
    district = find(r"([A-Za-zА-Яа-яЎўҚқҒғҲҳ`'\-]+)\s*(?:tumani|туман)", addr) or \
               find(r"([A-Za-zА-Яа-яЎўҚқҒғҲҳ`'\-]+)\s*shahar", addr)
    return region_code, district


def parse_lot(raw: dict) -> dict | None:
    text = raw.get("text", "")
    if not text or "error" in raw:
        return None
    lot_id = raw.get("lot_id")

    address = find(r"Manzil:\s*\n?([^\n]+)", text)
    region, district = detect_region(address)

    start_price = num(find(r"Boshlang[`'‘’ʼ]ich narxi:\s*\n?([\d\s.,]+)\s*UZS", text))
    deposit = num(find(r"Zakalat puli miqdori[^:]*:\s*\n?([\d\s.,]+)\s*UZS", text))

    auction_method = find(r"Savdo o[`'‘’ʼ]tkazish turi:\s*\n?([^\n]+)", text)
    auction_style = find(r"Savdo o[`'‘’ʼ]tkazish uslubi:\s*\n?([^\n]+)", text)

    start_time = find(r"Savdo boshlanish vaqti:\s*\n?(\d{2}\.\d{2}\.\d{4}\s*\d{2}:\d{2})", text)
    deadline = find(r"Arizalarni qabul qilishning oxirgi muddati:\s*\n?(\d{2}\.\d{2}\.\d{4}\s*\d{2}:\d{2})", text)
    end_time = find(r"Savdo tugash vaqti:\s*\n?(\d{2}\.\d{2}\.\d{4}\s*\d{2}:\d{2})", text)

    status = find(r"Lot holati:\s*\n?([^\n]+)", text)

    # Lot type from breadcrumb
    crumbs = re.findall(r"chevron_right\s*\n([^\n]+)", text)
    lot_type = crumbs[2] if len(crumbs) >= 3 else (crumbs[1] if len(crumbs) >= 2 else None)
    lot_type_specific = crumbs[3] if len(crumbs) >= 4 else None

    title = find(r"Lot\s*№\s*\n?\s*\d+\s*\n([^\n]+)", text)

    # Views/eye count (after remove_red_eye icon)
    views = num(find(r"remove_red_eye\s*\n\s*(\d+)", text))

    # Bidders count if shown
    bidders = num(find(r"Ishtirokchilar soni[:\s]*\s*(\d+)", text))

    # Check closed/open keywords
    auction_type = "open"
    text_lower = text.lower()
    if "yopiq auksion" in text_lower or "ёпиқ аукцион" in text_lower or "yopiq tanlov" in text_lower:
        auction_type = "closed"

    # Seller heuristic
    seller_hint = None
    if "davlat aktivlari" in text_lower or "davaktiv" in text_lower:
        seller_hint = "davaktiv"
    elif "sud" in text_lower and "ijro" in text_lower:
        seller_hint = "court"
    elif "bank" in text_lower:
        seller_hint = "bank"

    # Step price
    step_price = num(find(r"Birinchi qadam bahosi[^:]*:\s*\n?([\d\s.,]+)\s*UZS", text))

    # Installment months
    installment = find(r"(\d+)\s*oy\s*\n*\s*Muddatli bo[`'‘’ʼ]lib", text)

    return {
        "lot_id": lot_id,
        "url": raw.get("url"),
        "title": title,
        "lot_type": lot_type,
        "lot_type_specific": lot_type_specific,
        "address": address,
        "region": region,
        "district": district,
        "start_price": start_price,
        "deposit": deposit,
        "step_price": step_price,
        "installment_months": int(installment) if installment else None,
        "auction_method": auction_method,
        "auction_style": auction_style,
        "auction_type": auction_type,
        "start_time": start_time,
        "deadline": deadline,
        "end_time": end_time,
        "status": status,
        "views": int(views) if views else None,
        "bidders_count": int(bidders) if bidders else None,
        "seller_hint": seller_hint,
    }


def main():
    raw_path = ROOT / "data" / "lots_raw.json"
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
    with_price = sum(1 for p in parsed if p.get("start_price"))
    with_region = sum(1 for p in parsed if p.get("region"))
    print(f"  has start_price: {with_price}")
    print(f"  has region: {with_region}")


if __name__ == "__main__":
    main()
