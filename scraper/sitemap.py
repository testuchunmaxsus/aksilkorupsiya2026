"""Sitemap parser — e-auksion.uz public sitemap'idan lot ID'larni oladi.

E-auksion'da 23 milliondan ortiq lot bor va sitemap public — har kim oladi.
Bu skript scraper pipeline'ning birinchi bosqichi: ID'larni ro'yxat qilib qo'yamiz,
keyin api_scraper bu ID'lar bo'yicha har lotning ma'lumotini oladi.
"""
import xml.etree.ElementTree as ET
import httpx
import json
from pathlib import Path

# XML namespace — sitemaps.org rasmiy schema
NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

# 3 ta sitemap part'ga bo'lingan (Google bo'yicha har 50K URL — alohida fayl)
SITEMAPS = [
    "https://e-auksion.uz/sitemap_new_lots_part1.xml",
    "https://e-auksion.uz/sitemap_new_lots_part2.xml",
    "https://e-auksion.uz/sitemap_new_lots_part3.xml",
]

# User-Agent — odamga o'xshash (haqiqiy brauzer headerini taqlid qilish)
HEADERS = {"User-Agent": "Mozilla/5.0 AuksionWatch/0.1 (research)"}


def fetch_lot_ids(limit: int | None = None) -> list[dict]:
    """Sitemap'lardan lot ID'larni oladi va ro'yxat qaytaradi.

    Args:
        limit: agar berilsa, shu miqdordan keyin to'xtaydi (test uchun foydali)

    Returns:
        [{"lot_id": int, "lastmod": "2026-04-25T...", "url": "https://..."}, ...]
    """
    out = []
    with httpx.Client(timeout=30, headers=HEADERS, follow_redirects=True) as client:
        for url in SITEMAPS:
            print(f"[sitemap] fetching {url}")
            r = client.get(url)
            r.raise_for_status()  # HTTP xato bo'lsa exception
            # XML'ni parse qilish
            root = ET.fromstring(r.content)
            # Har <url> elementidan <loc> va <lastmod> ni olamiz
            for u in root.findall("sm:url", NS):
                loc = u.find("sm:loc", NS).text  # "https://e-auksion.uz/lot-view?lot_id=12345"
                lastmod = u.find("sm:lastmod", NS).text if u.find("sm:lastmod", NS) is not None else None
                # URL'dan lot_id=NNN qismini ajratib olish
                lot_id = int(loc.split("lot_id=")[1])
                out.append({"lot_id": lot_id, "lastmod": lastmod, "url": loc})
                # Limit yetganda erta to'xtaymiz
                if limit and len(out) >= limit:
                    return out
    return out


def main():
    """CLI entry — `python -m scraper.sitemap --limit 1000 --out ...`."""
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=None,
                   help="Necha ID olish (default: hammasi)")
    p.add_argument("--out", default="../data/lot_ids.json",
                   help="Natija JSON fayli")
    args = p.parse_args()

    ids = fetch_lot_ids(limit=args.limit)
    # Ota-papkani yaratamiz (mavjud bo'lmasa)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    # JSON'ga saqlash — UTF-8, indented, hech qanday escape bo'lmaydi (kiril/lotin)
    Path(args.out).write_text(json.dumps(ids, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[sitemap] saved {len(ids)} lot IDs -> {args.out}")


if __name__ == "__main__":
    main()
