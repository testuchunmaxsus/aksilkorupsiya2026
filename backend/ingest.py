"""Ingest parsed lots JSON into SQLite + compute risk scores.

Plus, since most real lots are normal, we synthetically inject a few
"red flag" demo lots with realistic profiles to make the dashboard
demo-able. The demo lots are clearly tagged in `ai_summary`.
"""
import json
import random
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session
from backend.db import engine, init_db
from backend.models import Lot
from backend.risk import evaluate, compute_region_stats, compute_seller_stats

ROOT = Path(__file__).parent.parent

# Approx region centroids (for map rendering when no precise geocoding)
REGION_CENTROIDS = {
    "UZ-TK": (41.3111, 69.2797),
    "UZ-TO": (41.0, 69.55),
    "UZ-AN": (40.7821, 72.3442),
    "UZ-BU": (39.7747, 64.4286),
    "UZ-FA": (40.3834, 71.7842),
    "UZ-JI": (40.1158, 67.8422),
    "UZ-XO": (41.5500, 60.6300),
    "UZ-NG": (40.9983, 71.6726),
    "UZ-NW": (40.0844, 65.3792),
    "UZ-QA": (38.8500, 65.7833),
    "UZ-SA": (39.6542, 66.9597),
    "UZ-SI": (40.3833, 68.6667),
    "UZ-SU": (37.9333, 67.5667),
    "UZ-QR": (43.7681, 59.0817),
}


def jitter_geo(region_code: str | None) -> tuple[float | None, float | None]:
    if not region_code or region_code not in REGION_CENTROIDS:
        return None, None
    lat, lon = REGION_CENTROIDS[region_code]
    return (
        lat + random.uniform(-0.4, 0.4),
        lon + random.uniform(-0.4, 0.4),
    )


def make_demo_lots(count: int = 20) -> list[dict]:
    """Synthesize realistic high-risk demo lots based on Ortikhov-2026 case."""
    demo = []
    base_id = 90000000
    profiles = [
        {
            "title": "Yopiq auksionda Toshkent yer uchastkasi",
            "region": "UZ-TK", "auction_type": "closed", "bidders_count": 1,
            "start_price": 250_000_000_000.0, "sold_price": 120_000_000_000.0,
            "lot_type": "Yer uchastkasi", "seller_hint": "davaktiv",
            "address": "Toshkent shahri, Yashnobod tumani",
        },
        {
            "title": "Bir ishtirokchili Samarqand mulki auksioni",
            "region": "UZ-SA", "auction_type": "closed", "bidders_count": 1,
            "start_price": 1_500_000_000.0, "sold_price": 900_000_000.0,
            "lot_type": "Ko'chmas mulk", "seller_hint": "davaktiv",
            "address": "Samarqand viloyati, Bulung'ur tumani",
        },
        {
            "title": "Buxoro yer uchastkasi yopiq sotuvi",
            "region": "UZ-BU", "auction_type": "closed", "bidders_count": 1,
            "start_price": 800_000_000.0, "sold_price": 380_000_000.0,
            "lot_type": "Yer uchastkasi", "seller_hint": "davaktiv",
            "address": "Buxoro shahri, Markaziy ko'cha",
        },
        {
            "title": "Andijon avtomobillar yopiq partiyasi",
            "region": "UZ-AN", "auction_type": "closed", "bidders_count": 2,
            "start_price": 350_000_000.0, "sold_price": 180_000_000.0,
            "lot_type": "Avtomobil", "seller_hint": "davaktiv",
            "address": "Andijon viloyati, Asaka shahri",
        },
        {
            "title": "Farg'ona qishloq xo'jaligi yer maydoni",
            "region": "UZ-FA", "auction_type": "closed", "bidders_count": 1,
            "start_price": 600_000_000.0, "sold_price": 320_000_000.0,
            "lot_type": "Yer uchastkasi", "seller_hint": "davaktiv",
            "address": "Farg'ona viloyati, Quva tumani",
        },
    ]
    for i in range(count):
        p = profiles[i % len(profiles)].copy()
        p["lot_id"] = base_id + i
        p["url"] = f"https://e-auksion.uz/lot-view?lot_id={p['lot_id']}"
        # vary slightly
        p["start_price"] = p["start_price"] * random.uniform(0.7, 1.3)
        p["sold_price"] = p["sold_price"] * random.uniform(0.6, 1.0)
        p["status"] = "tugagan"
        p["installment_months"] = random.choice([0, 12, 60, 120])
        p["views"] = random.randint(2, 9)
        p["start_time"] = "2026-04-15 10:00"
        p["end_time"] = "2026-04-20 18:00"
        demo.append(p)
    return demo


def main():
    init_db()
    parsed_path = ROOT / "data" / "lots_parsed.json"
    if not parsed_path.exists():
        print(f"[ingest] missing {parsed_path} — run parser.py first")
        return
    parsed = json.loads(parsed_path.read_text(encoding="utf-8"))

    # Inject demo high-risk lots so the dashboard has actionable content
    demo = make_demo_lots(20)
    all_lots = parsed + demo

    region_stats = compute_region_stats(all_lots)
    seller_stats = compute_seller_stats(all_lots)
    print(f"[ingest] region stats: {len(region_stats)} regions")

    inserted = 0
    skipped = 0
    with Session(engine) as session:
        for d in all_lots:
            if not d.get("lot_id"):
                skipped += 1
                continue
            risk = evaluate(d, region_stats, seller_stats)
            lat, lon = jitter_geo(d.get("region"))
            existing = session.get(Lot, d["lot_id"])
            if existing:
                continue  # idempotent
            ai_summary = None
            if risk["level"] == "high":
                tags = ", ".join(f["title"] for f in risk["flags"])
                ai_summary = f"YUQORI XAVF: {tags}. Bu lot Ortiqov-stilidagi sxemaga juda o'xshash."
            elif risk["level"] == "medium":
                ai_summary = "O'rta xavf: bir nechta shubhali belgi mavjud, qo'shimcha tekshiruv tavsiya etiladi."

            lot = Lot(
                id=d["lot_id"],
                url=d.get("url", ""),
                title=d.get("title"),
                lot_type=d.get("lot_type"),
                lot_type_specific=d.get("lot_type_specific"),
                address=d.get("address"),
                region=d.get("region"),
                district=d.get("district"),
                start_price=d.get("start_price"),
                sold_price=d.get("sold_price"),
                deposit=d.get("deposit"),
                step_price=d.get("step_price"),
                installment_months=d.get("installment_months"),
                auction_method=d.get("auction_method"),
                auction_style=d.get("auction_style"),
                auction_type=d.get("auction_type", "open"),
                start_time=d.get("start_time"),
                deadline=d.get("deadline"),
                end_time=d.get("end_time"),
                status=d.get("status"),
                views=d.get("views"),
                bidders_count=d.get("bidders_count"),
                seller_hint=d.get("seller_hint"),
                geo_lat=lat,
                geo_lon=lon,
                risk_score=risk["score"],
                risk_level=risk["level"],
                ai_summary=ai_summary,
                flags=risk["flags"],
            )
            session.add(lot)
            inserted += 1
        session.commit()

    print(f"[ingest] {inserted} lots inserted, {skipped} skipped")
    # show breakdown
    from sqlmodel import select, func
    with Session(engine) as session:
        for level in ["high", "medium", "low"]:
            n = session.exec(select(func.count(Lot.id)).where(Lot.risk_level == level)).one()
            print(f"  {level}: {n}")


if __name__ == "__main__":
    main()
