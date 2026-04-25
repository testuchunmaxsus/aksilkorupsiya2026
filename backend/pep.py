"""PEP (Politically Exposed Persons) detection.

FATF Recommendation 12 + EU 4-AML Directive bo'yicha mansabdor screening.
Sotuvchi nomini watchlist (data/pep_watchlist.json) bilan solishtiradi va:
  - exact   — to'liq mos
  - alias   — kiril/lotin variant
  - fuzzy   — 85%+ o'xshash (yashirin urinish)
  - family  — familiya bir xil (oila a'zosi)
holatlarini topadi.
"""
import json
import re
import unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable

# PEP watchlist faylining yo'li (loyiha root'idagi data/ ichida)
WATCHLIST_PATH = Path(__file__).parent.parent / "data" / "pep_watchlist.json"


def normalize(s: str | None) -> str:
    """Ism/familiyani solishtirishga tayyorlash.

    Bajaradi:
      - Unicode NFKD dekompozitsiya (è → e + ̀ → e)
      - Diakritikalarni olib tashlash
      - Katta harflarga o'tkazish
      - Apostrof variantlarini olib tashlash (` ' ‘ ’ ʼ — Cyrillic+Latin uchun)
      - Ortiqcha bo'shliqlarni qisqartirish
    """
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.upper()
    for ch in "`'‘’ʼ":
        s = s.replace(ch, "")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def last_name(s: str) -> str:
    """Familiyani ajratib oladi (O'zbekistonda odatda birinchi so'z)."""
    n = normalize(s)
    parts = n.split()
    return parts[0] if parts else ""


def fuzzy(a: str, b: str) -> float:
    """Ikki nom o'rtasidagi o'xshashlik koeffitsienti (0-1)."""
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


class PEPRegistry:
    """Watchlist'ni xotirada saqlovchi va tezkor matching qiluvchi singleton."""

    def __init__(self, path: Path = WATCHLIST_PATH):
        # Fayl yo'q bo'lsa — bo'sh registry (test/lokal develop holatlari)
        if not path.exists():
            self.officials = []
            self.gov_address_keywords = []
            self.family_keywords = []
            return

        # JSON'dan yuklash
        data = json.loads(path.read_text(encoding="utf-8"))
        self.officials = data.get("officials", [])
        self.gov_address_keywords = data.get("government_addresses", [])
        self.family_keywords = data.get("family_keywords", [])

        # Tezkor matching uchun normallashtirilgan ismlarni oldindan hisoblash
        for o in self.officials:
            o["_n_name"] = normalize(o["name"])
            o["_n_aliases"] = [normalize(a) for a in (o.get("aliases") or [])]
            o["_last_name"] = last_name(o["name"])

    def match(self, seller_name: str | None) -> dict | None:
        """Sotuvchi nomini PEP watchlist bilan solishtiradi.

        4 tartibda tekshiradi (yuqoridan pastga):
          1. Exact      — to'liq mos (similarity=1.0)
          2. Alias      — Cyrillic/Latin variant (similarity=0.95)
          3. Fuzzy      — 85%+ o'xshash (yashirin urinish bo'lishi mumkin)
          4. Family     — familiya mos (oila a'zosi taxmini, FATF R12)

        Returns: {pep_id, pep_name, match_type, similarity, ...} yoki None
        """
        if not seller_name:
            return None
        sn = normalize(seller_name)
        sn_last = last_name(seller_name)

        best = None
        for o in self.officials:
            # 1. Exact ism — eng kuchli mos
            if sn == o["_n_name"]:
                return {
                    "pep_id": o["id"],
                    "pep_name": o["name"],
                    "match_type": "exact",
                    "similarity": 1.0,
                    "category": o.get("category"),
                    "case_url": o.get("case_url"),
                    "case_summary": o.get("case_summary"),
                }
            # 2. Alias (Cyrillic/Latin transliteratsiya variantlari)
            if sn in o["_n_aliases"]:
                return {
                    "pep_id": o["id"],
                    "pep_name": o["name"],
                    "match_type": "alias",
                    "similarity": 0.95,
                    "category": o.get("category"),
                    "case_url": o.get("case_url"),
                    "case_summary": o.get("case_summary"),
                }
            # 3. Yuqori darajali fuzzy (>85% — yashirin urinish bo'lishi mumkin)
            ratio = fuzzy(seller_name, o["name"])
            if ratio > 0.85:
                cand = {
                    "pep_id": o["id"],
                    "pep_name": o["name"],
                    "match_type": "fuzzy",
                    "similarity": round(ratio, 3),
                    "category": o.get("category"),
                    "case_url": o.get("case_url"),
                    "case_summary": o.get("case_summary"),
                }
                if best is None or ratio > best["similarity"]:
                    best = cand
                continue
            # 4. Familiya mos — oila a'zosi taxmini
            if o["_last_name"] and sn_last and sn_last == o["_last_name"]:
                cand = {
                    "pep_id": o["id"],
                    "pep_name": o["name"],
                    "match_type": "family_lastname",
                    "similarity": 0.7,
                    "category": o.get("category"),
                    "case_url": o.get("case_url"),
                    "case_summary": o.get("case_summary"),
                }
                if best is None:
                    best = cand
        return best

    def is_government_address(self, address: str | None) -> str | None:
        """Manzilda davlat ofisi kalit so'zlari bormi?

        'hokimligi', 'vazirligi', 'agentligi' kabi so'zlar topilsa —
        insider self-dealing belgisi (World Bank IACRC).
        """
        if not address:
            return None
        a = normalize(address)
        for entry in self.gov_address_keywords:
            for kw in entry.get("keywords", []):
                if normalize(kw) in a:
                    return entry.get("type")  # masalan "regional_admin"
        return None


def family_clusters(lots: Iterable[dict], min_count: int = 3) -> dict[str, list]:
    """Bir xil familiyali sotuvchilarni topish (qarindoshlik tarmog'i taxmini).

    3+ ta unikal sotuvchi bir familiya bilan ro'yxatda bo'lsa — klaster.
    Misol: 'NIYOZOV' familiyasi 5 ta turli seller_id bilan → klaster.

    Returns: {familiya: [seller_id1, seller_id2, ...]}
    """
    by_last = defaultdict(list)
    for l in lots:
        if l.get("seller_name"):
            ln = last_name(l["seller_name"])
            # Juda qisqa familiya — typo bo'lishi mumkin, o'tkazib yuboramiz
            if ln and len(ln) >= 4:
                by_last[ln].append({
                    "seller_id": l.get("seller_id"),
                    "seller_name": l["seller_name"],
                    "lot_id": l.get("lot_id") or l.get("id"),
                })

    # Faqat 3+ unikal seller_id bo'lgan familiyalarni saqlaymiz
    out = {}
    for ln, rows in by_last.items():
        unique_sellers = {r["seller_id"] for r in rows if r["seller_id"]}
        if len(unique_sellers) >= min_count:
            out[ln] = list(unique_sellers)
    return out


# Singleton instance — bir marta yuklanadi, qayta-qayta ishlatiladi
_REGISTRY = None


def get_registry() -> PEPRegistry:
    """Lazy-loaded PEP registry. Birinchi chaqiruvda fayl o'qiladi."""
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = PEPRegistry()
    return _REGISTRY
