"""Recompute risk scores for ALL lots already in DB using v1.1 engine.

Pulls from DB, re-evaluates with full global stats, writes back categories.
"""
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select, func
from backend.db import engine
from backend.models import Lot
from backend.risk import evaluate, compute_region_stats, compute_seller_stats
from backend.pep import family_clusters as pep_family_clusters


def lot_to_dict(lot: Lot) -> dict:
    return {
        "lot_id": lot.id,
        "title": lot.title,
        "lot_type": lot.lot_type,
        "lot_type_specific": lot.lot_type_specific,
        "address": lot.address,
        "region": lot.region,
        "district": lot.district,
        "start_price": lot.start_price,
        "sold_price": lot.sold_price,
        "appraised_price": lot.appraised_price,
        "deposit": lot.deposit,
        "step_price": lot.step_price,
        "installment_months": lot.installment_months,
        "auction_type": lot.auction_type,
        "auction_method": lot.auction_method,
        "start_time": lot.start_time,
        "end_time": lot.end_time,
        "views": lot.views,
        "bidders_count": lot.bidders_count,
        "times_auctioned": lot.times_auctioned,
        "seller_hint": lot.seller_hint,
        "seller_id": lot.seller_id,
        "seller_name": lot.seller_name,
        "is_descending": lot.is_descending,
    }


def main():
    with Session(engine) as session:
        all_lots = session.exec(select(Lot)).all()
        print(f"[rescore] {len(all_lots)} lots in DB")

        as_dicts = [lot_to_dict(l) for l in all_lots]
        region_stats = compute_region_stats(as_dicts)
        seller_stats = compute_seller_stats(as_dicts)
        family_clusters_dict = pep_family_clusters(as_dicts, min_count=3)
        family_keys = set(family_clusters_dict.keys())
        print(f"[rescore] regions: {len(region_stats)}, sellers: {len(seller_stats)}, family clusters: {len(family_keys)}")

        levels = defaultdict(int)
        cat_lot_counts = defaultdict(int)
        for lot in all_lots:
            d = lot_to_dict(lot)
            risk = evaluate(d, region_stats, seller_stats, family_clusters=family_keys)
            lot.risk_score = risk["score"]
            lot.risk_level = risk["level"]
            lot.flags = risk["flags"]
            lot.categories = risk["categories"]
            if risk["level"] == "high":
                top = ", ".join(f["title"] for f in risk["flags"][:3])
                lot.ai_summary = (
                    f"YUQORI XAVF ({risk['score']:.0f}/100): {top}. "
                    "Bu lot Ortikhov-stilidagi sxemaga o'xshash patternga ega."
                )
            elif risk["level"] == "medium":
                lot.ai_summary = (
                    f"O'RTA XAVF ({risk['score']:.0f}/100): {len(risk['flags'])} ta shubhali belgi."
                )
            else:
                lot.ai_summary = None
            levels[risk["level"]] += 1
            for cat, val in risk["categories"].items():
                if val > 0:
                    cat_lot_counts[cat] += 1

        session.commit()

    print(f"[rescore] levels: {dict(levels)}")
    print(f"[rescore] lots with at least one signal per category:")
    for cat in "ABCDE":
        print(f"  {cat}: {cat_lot_counts[cat]}")

    with Session(engine) as session:
        total = session.exec(select(func.count(Lot.id))).one()
        high = session.exec(select(func.count(Lot.id)).where(Lot.risk_level == "high")).one()
        medium = session.exec(select(func.count(Lot.id)).where(Lot.risk_level == "medium")).one()
        print(f"\n[db] total: {total}, high: {high}, medium: {medium}")


if __name__ == "__main__":
    main()
