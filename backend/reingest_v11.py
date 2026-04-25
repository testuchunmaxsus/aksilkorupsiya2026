"""v1.1 re-ingest: rebuild risk scores using new categorized engine.

Sources combined:
1. data/lots_parsed.json — Excel-derived (Farg'ona 9266 lots)
2. data/lots_api.json    — direct API scrape (~2000 lots, richer fields)
3. backend/ingest demo lots (20 high-risk synthesized)

Computes per-category sub-scores (A/B/C/D/E) and updates DB rows.
"""
import json
import sys
import random
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select, func
from backend.db import engine, init_db
from backend.models import Lot
from backend.risk import evaluate, compute_region_stats, compute_seller_stats

ROOT = Path(__file__).parent.parent

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


def jitter(region):
    if region not in REGION_CENTROIDS:
        return None, None
    lat, lon = REGION_CENTROIDS[region]
    return lat + random.uniform(-0.4, 0.4), lon + random.uniform(-0.4, 0.4)


def load_all_lots():
    """Load lots from all sources into a single dict[lot_id] -> dict."""
    lots = {}

    # 1. API-scraped (richer)
    api_path = ROOT / "data" / "lots_parsed.json"
    if api_path.exists():
        try:
            for r in json.loads(api_path.read_text(encoding="utf-8")):
                if r and r.get("lot_id"):
                    lots[r["lot_id"]] = r
            print(f"[load] from {api_path}: {len(lots)} lots (cumulative)")
        except Exception as e:
            print(f"[load] api parse error: {e}")

    # NOTE: synthetic demo lots removed for production. Real data only.
    return lots


def make_demo():
    """Synthetic Ortikhov-style demo lots."""
    profiles = [
        {"region": "UZ-TK", "title": "Yopiq auksionda Toshkent yer uchastkasi",
         "lot_type": "Yer uchastkasi", "auction_type": "closed", "bidders_count": 1,
         "start_price": 250e9, "sold_price": 120e9, "appraised_price": 280e9},
        {"region": "UZ-SA", "title": "Bir ishtirokchili Samarqand mulki",
         "lot_type": "Ko'chmas mulk", "auction_type": "closed", "bidders_count": 1,
         "start_price": 1.5e9, "sold_price": 0.9e9, "appraised_price": 1.8e9},
        {"region": "UZ-BU", "title": "Buxoro yer uchastkasi yopiq sotuvi",
         "lot_type": "Yer uchastkasi", "auction_type": "closed", "bidders_count": 1,
         "start_price": 0.8e9, "sold_price": 0.38e9, "appraised_price": 0.95e9},
        {"region": "UZ-AN", "title": "Andijon avtomobillar yopiq partiyasi",
         "lot_type": "Avtomobil", "auction_type": "closed", "bidders_count": 2,
         "start_price": 0.35e9, "sold_price": 0.18e9, "appraised_price": 0.4e9},
        {"region": "UZ-FA", "title": "Farg'ona qishloq xo'jaligi yer maydoni",
         "lot_type": "Yer uchastkasi", "auction_type": "closed", "bidders_count": 1,
         "start_price": 0.6e9, "sold_price": 0.32e9, "appraised_price": 0.7e9},
    ]
    out = []
    for i in range(20):
        p = profiles[i % len(profiles)].copy()
        p["lot_id"] = 90000000 + i
        p["url"] = f"https://e-auksion.uz/lot-view?lot_id={p['lot_id']}"
        p["start_price"] = p["start_price"] * random.uniform(0.7, 1.3)
        p["sold_price"] = p["sold_price"] * random.uniform(0.6, 1.0)
        p["appraised_price"] = p["appraised_price"] * random.uniform(0.95, 1.05)
        p["status"] = "tugagan"
        p["installment_months"] = random.choice([0, 12, 60, 120])
        p["views"] = random.randint(2, 9)
        p["start_time"] = "2026-04-15 10:00"
        p["end_time"] = "2026-04-20 18:00"
        p["seller_hint"] = "davaktiv"
        p["seller_id"] = 1000001 + (i % 3)
        p["seller_name"] = ["Davaktiv Toshkent", "Davaktiv Samarqand", "Davaktiv Buxoro"][i % 3]
        out.append(p)
    return out


def main():
    init_db()
    lots = load_all_lots()
    print(f"[load] total lots to score: {len(lots)}")

    # Compute global statistics
    region_stats = compute_region_stats(lots.values())
    seller_stats = compute_seller_stats(lots.values())
    print(f"[stats] regions: {len(region_stats)}, sellers: {len(seller_stats)}")

    # Re-ingest: update existing rows OR insert new
    updated = 0
    inserted = 0
    level_counter = {"low": 0, "medium": 0, "high": 0}
    cat_totals = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0}

    with Session(engine) as session:
        for lot_id, d in lots.items():
            risk = evaluate(d, region_stats, seller_stats)
            level_counter[risk["level"]] += 1
            for cat, val in risk["categories"].items():
                if val > 0:
                    cat_totals[cat] += 1

            ai_summary = None
            if risk["level"] == "high":
                top_titles = [f["title"] for f in risk["flags"][:3]]
                ai_summary = (
                    f"YUQORI XAVF ({risk['score']:.0f}/100): {', '.join(top_titles)}. "
                    "Bu lot Ortikhov-stilidagi sxemaga o'xshash patternga ega."
                )
            elif risk["level"] == "medium":
                ai_summary = f"O'RTA XAVF ({risk['score']:.0f}/100): {len(risk['flags'])} ta shubhali belgi."

            existing = session.get(Lot, lot_id)
            lat = d.get("geo_lat")
            lon = d.get("geo_lon")
            if (lat is None or lon is None) and d.get("region"):
                lat, lon = jitter(d["region"])

            payload = dict(
                id=lot_id,
                url=d.get("url") or f"https://e-auksion.uz/lot-view?lot_id={lot_id}",
                title=d.get("title"),
                lot_type=d.get("lot_type"),
                lot_type_specific=d.get("lot_type_specific"),
                address=d.get("address"),
                region=d.get("region"),
                district=d.get("district"),
                start_price=d.get("start_price"),
                sold_price=d.get("sold_price"),
                appraised_price=d.get("appraised_price"),
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
                times_auctioned=d.get("times_auctioned"),
                seller_hint=d.get("seller_hint"),
                seller_name=d.get("seller_name"),
                seller_id=d.get("seller_id"),
                geo_lat=lat,
                geo_lon=lon,
                is_descending=bool(d.get("is_descending")),
                risk_score=risk["score"],
                risk_level=risk["level"],
                ai_summary=ai_summary,
                flags=risk["flags"],
                categories=risk["categories"],
            )
            if existing:
                for k, v in payload.items():
                    if k != "id":
                        setattr(existing, k, v)
                updated += 1
            else:
                session.add(Lot(**payload))
                inserted += 1

            if (updated + inserted) % 500 == 0:
                session.commit()
                print(f"  processed {updated + inserted}...")

        session.commit()

    print(f"\n[reingest] DONE")
    print(f"  updated:  {updated}")
    print(f"  inserted: {inserted}")
    print(f"  levels:   {level_counter}")
    print(f"  categories with at least one signal: {cat_totals}")

    with Session(engine) as session:
        total = session.exec(select(func.count(Lot.id))).one()
        high = session.exec(select(func.count(Lot.id)).where(Lot.risk_level == "high")).one()
        medium = session.exec(select(func.count(Lot.id)).where(Lot.risk_level == "medium")).one()
        print(f"\n[db] total: {total}, high: {high}, medium: {medium}")


if __name__ == "__main__":
    main()
