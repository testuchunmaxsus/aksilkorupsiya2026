"""Sitemap parser — fetch lot IDs from e-auksion.uz public sitemap."""
import xml.etree.ElementTree as ET
import httpx
import json
from pathlib import Path

NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
SITEMAPS = [
    "https://e-auksion.uz/sitemap_new_lots_part1.xml",
    "https://e-auksion.uz/sitemap_new_lots_part2.xml",
    "https://e-auksion.uz/sitemap_new_lots_part3.xml",
]
HEADERS = {"User-Agent": "Mozilla/5.0 AuksionWatch/0.1 (research)"}


def fetch_lot_ids(limit: int | None = None) -> list[dict]:
    out = []
    with httpx.Client(timeout=30, headers=HEADERS, follow_redirects=True) as client:
        for url in SITEMAPS:
            print(f"[sitemap] fetching {url}")
            r = client.get(url)
            r.raise_for_status()
            root = ET.fromstring(r.content)
            for u in root.findall("sm:url", NS):
                loc = u.find("sm:loc", NS).text
                lastmod = u.find("sm:lastmod", NS).text if u.find("sm:lastmod", NS) is not None else None
                lot_id = int(loc.split("lot_id=")[1])
                out.append({"lot_id": lot_id, "lastmod": lastmod, "url": loc})
                if limit and len(out) >= limit:
                    return out
    return out


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--out", default="../data/lot_ids.json")
    args = p.parse_args()

    ids = fetch_lot_ids(limit=args.limit)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(ids, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[sitemap] saved {len(ids)} lot IDs -> {args.out}")


if __name__ == "__main__":
    main()
