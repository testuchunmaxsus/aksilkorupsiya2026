"""Davlat lotlarini DB'da kalit so'zlar bo'yicha qayta tasniflash.

Hozirgi DB'da deyarli barcha lotlar "yuridik shaxs" yoki "court" deb
belgilangan, chunki Excel default'i noto'g'ri edi (MIB hisobotini
"davaktiv" deb belgilab kelgan edik). Bu skript:

  1. seller_name'da "DAVAKTIV", "VAZIRLIK", "HOKIMLIK", "AGENTLIGI"
     kabi davlat tashkilotlari kalit so'zlari bor lotlarni topadi
  2. ularni seller_hint="davaktiv" deb qayta belgilaydi
  3. risk score'larni qayta hisoblaydi (yangi seller_hint kontekstida)

Foydalanish:
    python -m backend.reclassify_state           # dry-run (faqat son ko'rsatadi)
    python -m backend.reclassify_state --apply   # haqiqatan o'zgartiradi
"""
import argparse
import sys
from sqlalchemy import or_, func
from sqlmodel import Session, select

from backend.db import engine
from backend.models import Lot

# Davlat tashkilotlari — seller_name ichida bor bo'lsa "davaktiv" deb belgilanadi.
# Lotin va Kirill harfli variantlar.
STATE_KEYWORDS = [
    "DAVAKTIV", "ДАВАКТИВ",
    "DAVLAT AKTIVLARI", "ГОСУДАРСТВЕННЫХ АКТИВОВ",
    "VAZIRLIK", "ВАЗИРЛИК", "ВАЗИРЛИГИ", "VAZIRLIGI",
    "MINISTERSTV", "МИНИСТЕРСТВ",
    "HOKIMLIGI", "HOKIMLIK", "ХОКИМЛИК", "ХОКИМЛИГИ",
    "ХОКИМИЯТ", "HOKIMIYATI",
    "AGENTLIGI", "АГЕНТЛИГИ", "АГЕНТСТВ", "AGENTLIK",
    "QO'MITASI", "ҚЎМИТАСИ", "КОМИТЕТ",
    "BOSHQARMASI", "БОШҚАРМАСИ", "УПРАВЛЕНИ",
    "INSPEKSIYA", "ИНСПЕКЦИ",
    "DEPARTAMENTI", "ДЕПАРТАМЕНТ",
    "TUMAN HOKIMLIGI", "VILOYAT HOKIMLIGI",
    "TUMAN MOLIYA", "VILOYAT MOLIYA",
    "DAVLAT MUASSASA", "ГОСУДАРСТВЕННОЕ УЧРЕЖДЕНИ",
    "DAVLAT KORXONA", "ГОСУДАРСТВЕННОЕ ПРЕДПРИЯТИ",
    "RESPUBLIKASI", "РЕСПУБЛИКИ",
    "TASHKENT SHAHAR HOKIM",
]


def find_state_lots(session: Session) -> list[Lot]:
    """seller_name yoki seller_address ichida davlat kalit so'zlari bor lotlarni topish."""
    conditions = []
    for kw in STATE_KEYWORDS:
        like = f"%{kw}%"
        conditions.append(Lot.seller_name.ilike(like))
        conditions.append(Lot.seller_address.ilike(like) if hasattr(Lot, "seller_address") else None)
    conditions = [c for c in conditions if c is not None]

    stmt = select(Lot).where(or_(*conditions))
    return list(session.exec(stmt).all())


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--apply", action="store_true", help="Haqiqatan o'zgartirish")
    p.add_argument("--limit", type=int, default=None, help="Faqat birinchi N lot")
    args = p.parse_args()

    with Session(engine) as session:
        # 1) Joriy taqsimot
        before_state = session.exec(
            select(func.count(Lot.id)).where(Lot.seller_hint == "davaktiv")
        ).one()
        before_total = session.exec(select(func.count(Lot.id))).one()
        print(f"\nJORIY HOLAT")
        print(f"  Jami lotlar: {before_total}")
        print(f"  davaktiv:    {before_state} ({before_state/before_total*100:.1f}%)")

        # 2) Davlat kalit so'zli lotlarni topish
        lots = find_state_lots(session)
        if args.limit:
            lots = lots[: args.limit]
        print(f"\nKALIT SO'Z BO'YICHA TOPILDI: {len(lots)} ta lot")

        # 3) Eng ko'p uchragan seller_name'larni ko'rsatish
        from collections import Counter
        names = Counter(l.seller_name for l in lots if l.seller_name)
        print(f"\nTOP 15 davlat sotuvchilari:")
        for name, cnt in names.most_common(15):
            short = (name or "")[:70]
            print(f"  {cnt:4d}  {short}")

        # 4) Ularning hozirgi seller_hint taqsimoti
        hints = Counter(l.seller_hint for l in lots)
        print(f"\nUlarning HOZIRGI seller_hint:")
        for hint, cnt in hints.most_common():
            print(f"  {cnt:5d}  {hint}")

        if not args.apply:
            print(f"\n--apply yo'q — o'zgartirilmadi. Haqiqatan qilish uchun:")
            print(f"  python -m backend.reclassify_state --apply")
            return

        # 5) APPLY — seller_hint = "davaktiv"
        changed = 0
        for lot in lots:
            if lot.seller_hint != "davaktiv":
                lot.seller_hint = "davaktiv"
                session.add(lot)
                changed += 1
        session.commit()

        # Yakuniy holat
        after_state = session.exec(
            select(func.count(Lot.id)).where(Lot.seller_hint == "davaktiv")
        ).one()
        print(f"\nO'ZGARTIRILDI: {changed} lot -> seller_hint='davaktiv'")
        print(f"YANGI HOLAT")
        print(f"  davaktiv: {before_state} -> {after_state} ({after_state/before_total*100:.1f}%)")
        print(f"\nKEYINGI QADAM - risk score qayta hisoblash:")
        print(f"  python -m backend.rescore_all")


if __name__ == "__main__":
    main()
