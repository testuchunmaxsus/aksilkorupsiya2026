"""PEP (Politically Exposed Persons) detection — fuzzy name matching + family/address checks.

Implements FATF Recommendation 12 + EU 4-AML Directive screening pattern.
"""
import json
import re
import unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable

WATCHLIST_PATH = Path(__file__).parent.parent / "data" / "pep_watchlist.json"


def normalize(s: str | None) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.upper()
    # Remove apostrophes and similar
    for ch in "`'‘’ʼ":
        s = s.replace(ch, "")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def last_name(s: str) -> str:
    n = normalize(s)
    parts = n.split()
    return parts[0] if parts else ""


def fuzzy(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


class PEPRegistry:
    def __init__(self, path: Path = WATCHLIST_PATH):
        if not path.exists():
            self.officials = []
            self.gov_address_keywords = []
            self.family_keywords = []
            return
        data = json.loads(path.read_text(encoding="utf-8"))
        self.officials = data.get("officials", [])
        self.gov_address_keywords = data.get("government_addresses", [])
        self.family_keywords = data.get("family_keywords", [])

        # Pre-compute normalized names
        for o in self.officials:
            o["_n_name"] = normalize(o["name"])
            o["_n_aliases"] = [normalize(a) for a in (o.get("aliases") or [])]
            o["_last_name"] = last_name(o["name"])

    def match(self, seller_name: str | None) -> dict | None:
        """Return best PEP match or None.

        Returns: {pep_id, pep_name, match_type, similarity}
        """
        if not seller_name:
            return None
        sn = normalize(seller_name)
        sn_last = last_name(seller_name)

        best = None
        for o in self.officials:
            # 1. Exact name or alias
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
            # 2. High-fidelity fuzzy
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
            # 3. Last-name match (family suspicion)
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
        """Return matched government type or None."""
        if not address:
            return None
        a = normalize(address)
        for entry in self.gov_address_keywords:
            for kw in entry.get("keywords", []):
                if normalize(kw) in a:
                    return entry.get("type")
        return None


def family_clusters(lots: Iterable[dict], min_count: int = 3) -> dict[str, list]:
    """Group sellers by last name. Cluster ≥ min_count = potential family."""
    by_last = defaultdict(list)
    for l in lots:
        if l.get("seller_name"):
            ln = last_name(l["seller_name"])
            if ln and len(ln) >= 4:  # ignore single-letter mistakes
                by_last[ln].append({
                    "seller_id": l.get("seller_id"),
                    "seller_name": l["seller_name"],
                    "lot_id": l.get("lot_id") or l.get("id"),
                })
    # only keep clusters by 3+ DIFFERENT seller_ids
    out = {}
    for ln, rows in by_last.items():
        unique_sellers = {r["seller_id"] for r in rows if r["seller_id"]}
        if len(unique_sellers) >= min_count:
            out[ln] = list(unique_sellers)
    return out


# Singleton instance
_REGISTRY = None


def get_registry() -> PEPRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = PEPRegistry()
    return _REGISTRY
