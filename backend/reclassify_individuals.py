"""'individual' deb belgilangan lotlarni qayta tahlil qilish.

KONTEKST: Fargona Excel hisoboti aslida Davaktiv'ning regional MIB
(Majburiy Ijro Byurosi) hisoboti edi - sud orqali musodara qilingan
shaxsiy mol-mulk. Excel ingest noto'g'ri default bilan ularni
"individual" yoki "davaktiv" deb belgiladi.

Bu skript:
  1. seller_hint='individual' lotlarni topadi
  2. Davlat tashkiloti kalit so'zlari bo'lmaganlarni 'court' (MIB) qiladi
     - chunki Fargona Excel = MIB Fargona hisoboti edi
  3. Risk score qayta hisoblanadi (court kontekstida monopoly va PEP yo'q)

Ishlatish:
    python -m backend.reclassify_individuals          # dry-run
    python -m backend.reclassify_individuals --apply  # haqiqatan
"""
import argparse
from sqlalchemy import or_
from sqlmodel import Session, select, func

from backend.db import engine
from backend.models import Lot
from backend.reclassify_state import STATE_KEYWORDS


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--apply", action="store_true")
    args = p.parse_args()

    with Session(engine) as session:
        # individual lotlarni topish
        ind = session.exec(
            select(Lot).where(Lot.seller_hint == "individual")
        ).all()
        print(f"individual lotlar: {len(ind)}")

        # Davlat keyword bor lotlarni alohida (ehtimol davaktiv)
        # Qolganlarini court (MIB) qilamiz
        to_court = []
        to_state = []
        for lot in ind:
            name = (lot.seller_name or "").upper()
            if any(kw in name for kw in STATE_KEYWORDS):
                to_state.append(lot)
            else:
                to_court.append(lot)

        print(f"  -> davaktiv (davlat keyword): {len(to_state)}")
        print(f"  -> court (MIB - sud orqali):  {len(to_court)}")

        if not args.apply:
            print("\n--apply yo'q - haqiqatan o'zgartirish uchun --apply qo'shing")
            return

        for lot in to_state:
            lot.seller_hint = "davaktiv"
            session.add(lot)
        for lot in to_court:
            lot.seller_hint = "court"
            session.add(lot)
        session.commit()

        # Yakuniy taqsimot
        rows = session.exec(
            select(Lot.seller_hint, func.count(Lot.id))
            .group_by(Lot.seller_hint)
            .order_by(func.count(Lot.id).desc())
        ).all()
        print("\nYANGI TAQSIMOT:")
        for h, c in rows:
            print(f"  {h or '(NULL)':15s} {c}")


if __name__ == "__main__":
    main()
