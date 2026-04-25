"""Rules-based risk scoring engine — v1.2 with categories + PEP layer.

5 international categories (OECD/OCP standard):
  A — Low Transparency
  B — Collusion
  C — Bid-Rigging
  D — Fraud
  E — Low Competition

Each rule is tagged with category, score, weight, and provenance (source +
formula), so the UI can explain WHY a flag fires.
"""
from typing import Iterable
from datetime import datetime
import re

from backend.pep import get_registry, last_name


# International references for explainability.
# Each entry: short title, primary source, methodology, e-auksion data fields used.
SOURCE = {
    "closed_auction": {
        "ref": "OECD A · UNCAC Art.9 · Fazekas NOAP",
        "url": "https://transparency.eu/integrity-watch-red-flags/",
        "formula": "is_closed == 1 (e-auksion API field)",
        "fields": ["is_closed"],
        "note": "Faqat API'dan kelgan lotlar uchun aniqlanadi. Excel hisobotida bu maydon yo'q.",
    },
    "no_announcement": {
        "ref": "UNCAC Art.9 · Fazekas NCSPEC",
        "url": "https://www.unodc.org/unodc/en/treaties/CAC/",
        "formula": "not_announce_of_results == 1",
        "fields": ["not_announce_of_results"],
    },
    "short_deadline": {
        "ref": "EU Directive · Fazekas SUBMP",
        "url": "https://www.againstcorruption.eu/wp-content/uploads/2022/07/ERCAS-WP-65_2022_Koen_Public-procurement-in-the-European-Union.pdf",
        "formula": "(start_time − create_time) < 7 days",
        "fields": ["start_time", "create_time"],
    },
    "low_visibility": {
        "ref": "OECD A.5 · DOZORRO heuristic",
        "url": "https://ti-ukraine.org/en/news/dozorro-artificial-intelligence-to-find-violations-in-prozorro-how-it-works/",
        "formula": "view_count < 10 AND is_closed == 1",
        "fields": ["view_count", "is_closed"],
    },
    "seller_closed_pattern": {
        "ref": "OCDS Cardinal R005 · Fazekas BCONC",
        "url": "https://www.open-contracting.org/2024/06/12/cardinal-an-open-source-library-to-calculate-public-procurement-red-flags/",
        "formula": "share of seller's lots that are closed > 50%",
        "fields": ["seller_id", "is_closed"],
    },
    "monopoly_seller": {
        "ref": "Fazekas SDOM · OECD E.3 · zIndex.cz",
        "url": "https://www.govtransparency.eu/wp-content/uploads/2015/11/GTI_WP2015_2_Fazekas_Kocsis_151015.pdf",
        "formula": "seller_total_lots ≥ 1000 (regional dominance)",
        "fields": ["seller_id"],
    },
    "dominant_seller": {
        "ref": "Fazekas SDOM (mild) · zIndex.cz",
        "url": "https://www.govtransparency.eu/wp-content/uploads/2015/11/GTI_WP2015_2_Fazekas_Kocsis_151015.pdf",
        "formula": "seller_total_lots ≥ 300",
        "fields": ["seller_id"],
    },
    "single_bidder": {
        "ref": "Fazekas CRI (eng kuchli) · OECD C.3 · OCDS R001",
        "url": "https://www.sciencedirect.com/science/article/abs/pii/S0176268021001166",
        "formula": "auction_cnt ≤ 1",
        "fields": ["auction_cnt"],
    },
    "many_reauctions": {
        "ref": "OCP R008 · World Bank IACRC",
        "url": "https://documents1.worldbank.org/curated/en/223241573576857116/pdf/Warning-Signs-of-Fraud-and-Corruption-in-Procurement.pdf",
        "formula": "times_auctioned ≥ 15 (failed-tender pattern)",
        "fields": ["times_auctioned"],
    },
    "repeat_auction": {
        "ref": "OCP R008",
        "url": "https://www.open-contracting.org/wp-content/uploads/2024/12/OCP2024-RedFlagProcurement-1.pdf",
        "formula": "times_auctioned in [8, 14]",
        "fields": ["times_auctioned"],
    },
    "reauction": {
        "ref": "OCP R008 (mild)",
        "url": "https://www.open-contracting.org/wp-content/uploads/2024/12/OCP2024-RedFlagProcurement-1.pdf",
        "formula": "times_auctioned in [5, 7]",
        "fields": ["times_auctioned"],
    },
    "descending_auction": {
        "ref": "UNCITRAL Reverse Auction Ch.",
        "url": "https://uncitral.un.org/sites/uncitral.un.org/files/media-documents/uncitral/en/2011-model-law-on-public-procurement-e.pdf",
        "formula": "is_descending_auction == 1",
        "fields": ["is_descending_auction"],
    },
    "combo_single_closed": {
        "ref": "Fazekas CRI (combo bonus) — eng kuchli signal",
        "url": "https://www.govtransparency.eu/wp-content/uploads/2015/11/GTI_WP2015_2_Fazekas_Kocsis_151015.pdf",
        "formula": "is_closed == 1 AND auction_cnt ≤ 1",
        "fields": ["is_closed", "auction_cnt"],
    },
    "physical_only": {
        "ref": "EU eligibility narrow",
        "url": "https://transparency.eu/integrity-watch-red-flags/",
        "formula": "is_juridical_can_apply == 0 AND is_physical_can_apply == 0",
        "fields": ["is_juridical_can_apply", "is_physical_can_apply"],
    },
    "appraisal_severe": {
        "ref": "Forensic appraisal · OECD D.1 · Yukos case",
        "url": "https://link.springer.com/article/10.1057/palgrave.jba.2950062",
        "formula": "start_price / appraised_price < 0.3",
        "fields": ["start_price", "appraised_price (baholangan_narx)"],
    },
    "below_appraisal": {
        "ref": "Forensic appraisal · OECD D.1",
        "url": "https://link.springer.com/article/10.1057/palgrave.jba.2950062",
        "formula": "start_price / appraised_price < 0.5",
        "fields": ["start_price", "appraised_price"],
    },
    "deeply_underpriced": {
        "ref": "Brazil ALICE benchmark · Fazekas",
        "url": "https://kun.uz/en/news/2025/03/05/uzbekistan-to-use-ai-for-fraud-prevention-in-public-procurement",
        "formula": "start_price < region_median * 0.3",
        "fields": ["start_price", "region"],
    },
    "underpriced": {
        "ref": "Brazil ALICE (mild)",
        "url": "https://kun.uz/en/news/2025/03/05/uzbekistan-to-use-ai-for-fraud-prevention-in-public-procurement",
        "formula": "start_price < region_median * 0.5",
        "fields": ["start_price", "region"],
    },
    "deep_discount": {
        "ref": "World Bank D · sham auction pattern",
        "url": "https://documents1.worldbank.org/curated/en/223241573576857116/pdf/Warning-Signs-of-Fraud-and-Corruption-in-Procurement.pdf",
        "formula": "(start_price − sold_price) / start_price > 30%",
        "fields": ["start_price", "sold_price"],
    },
    "long_installment": {
        "ref": "Heuristic — favoritism via installment",
        "url": "https://www.unodc.org/documents/corruption/Publications/2013/Guidebook_on_anti-corruption_in_public_procurement_and_the_management_of_public_finances.pdf",
        "formula": "installment_months ≥ 60",
        "fields": ["term_month", "is_term_payment"],
    },
    "stuck_lot_pattern": {
        "ref": "Combo signal · Romania Tel Drum keys",
        "url": "https://www.romania-insider.com/liviu-dragnea-sent-court-corruption-case-2022",
        "formula": "times_auctioned ≥ 8 AND seller_total_lots ≥ 300",
        "fields": ["times_auctioned", "seller_id"],
    },
    "pep_seller": {
        "ref": "FATF R12 · EU 4-AML Directive · UNCAC Art.8",
        "url": "https://www.fatf-gafi.org/en/publications/Fatfrecommendations/Pep-Recommendation12.html",
        "formula": "seller_name matches PEP watchlist (exact / alias / fuzzy ≥ 0.85)",
        "fields": ["seller_name"],
    },
    "pep_family_match": {
        "ref": "FATF R12 (family) · TI Georgia 50 family cases",
        "url": "https://transparency.ge/en/post/corruption-risks-process-state-property-privatization",
        "formula": "seller last-name matches PEP last-name",
        "fields": ["seller_name"],
    },
    "government_address": {
        "ref": "World Bank IACRC · OECD D — insider self-dealing",
        "url": "https://guide.iacrc.org/detection/red-flags-of-corruption-bid-rigging-and-other-schemes/",
        "formula": "seller address contains 'hokimligi'/'vazirligi'/'agentligi'",
        "fields": ["seller_address"],
    },
    "family_cluster": {
        "ref": "TI Georgia · pattern detection",
        "url": "https://transparency.ge/en/post/corruption-risks-process-state-property-privatization",
        "formula": "≥3 sellers share the same last name (kinship cluster)",
        "fields": ["seller_name"],
    },
}


# Weights — based on Fazekas CRI, OECD, and World Bank consensus.
# 1.0 = standard. Higher = more reliable corruption indicator.
WEIGHT = {
    "single_bidder": 1.2,
    "combo_single_closed": 1.3,
    "closed_auction": 1.0,
    "no_announcement": 1.0,
    "short_deadline": 0.8,
    "monopoly_seller": 1.1,
    "appraisal_severe": 1.2,
    "below_appraisal": 0.9,
    "underpriced": 0.9,
    "deeply_underpriced": 1.0,
    "deep_discount": 0.9,
    "many_reauctions": 1.0,
    "repeat_auction": 0.8,
    "reauction": 0.6,
    "long_installment": 0.4,
    "low_visibility": 0.4,
    "descending_auction": 0.7,
    "seller_closed_pattern": 0.9,
    "dominant_seller": 0.8,
    "stuck_lot_pattern": 0.7,
    "physical_only": 0.6,
    "pep_seller": 1.4,           # strongest insider signal
    "pep_family_match": 1.1,
    "government_address": 1.0,
    "family_cluster": 0.9,
}


def parse_date_uz(s: str | None) -> datetime | None:
    """Parse '12.05.2026 10:00' or '12.05.2026' or '2026-05-12 10:00:00'."""
    if not s or not isinstance(s, str):
        return None
    s = s.strip()
    fmts = [
        "%d.%m.%Y %H:%M",
        "%d.%m.%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ]
    for f in fmts:
        try:
            return datetime.strptime(s, f)
        except ValueError:
            continue
    # try "2026-05-12 10:00:00.0" with milliseconds
    s2 = re.sub(r"\.\d+$", "", s)
    for f in fmts:
        try:
            return datetime.strptime(s2, f)
        except ValueError:
            continue
    return None


def evaluate(
    lot: dict,
    region_stats: dict | None = None,
    seller_stats: dict | None = None,
    family_clusters: set[str] | None = None,
) -> dict:
    """Evaluate one lot, return {score, level, flags} with categorized flags."""
    flags: list[dict] = []
    pep_registry = get_registry()

    # ───────── A. LOW TRANSPARENCY ─────────
    is_closed = lot.get("auction_type") == "closed"
    if is_closed:
        flags.append({
            "type": "closed_auction",
            "category": "A",
            "score": 30,
            "title": "Yopiq auksion",
            "desc": "Lot yopiq auksionga chiqarilgan — kim ishtirok etganligi noma'lum.",
        })

    if lot.get("not_announce_of_results"):
        flags.append({
            "type": "no_announcement",
            "category": "A",
            "score": 20,
            "title": "Natija e'lon qilinmaydi",
            "desc": "Tender natijalari rasmiy e'lon qilinmagan — UNCAC Art.9 buzilishi.",
        })

    create = parse_date_uz(lot.get("create_time"))
    start = parse_date_uz(lot.get("start_time") or lot.get("start_time_str"))
    if create and start:
        days = (start - create).days
        if 0 <= days < 3:
            flags.append({
                "type": "short_deadline",
                "category": "A",
                "score": 25,
                "title": f"Juda qisqa muddat ({days} kun)",
                "desc": "Taklif berish muddati 3 kundan kam — raqobatchilarga vaqt yetmaydi.",
            })
        elif 3 <= days < 7:
            flags.append({
                "type": "short_deadline",
                "category": "A",
                "score": 15,
                "title": f"Qisqa muddat ({days} kun)",
                "desc": "Taklif berish muddati 7 kundan kam.",
            })

    views = lot.get("views") or 0
    if is_closed and views < 10:
        flags.append({
            "type": "low_visibility",
            "category": "A",
            "score": 7,
            "title": "Past ko'rishlar",
            "desc": f"Lot atigi {views} marta ko'rilgan — keng e'lon qilinmagan.",
        })

    # ───────── B. COLLUSION ─────────
    if seller_stats and lot.get("seller_hint"):
        st = seller_stats.get(lot["seller_hint"])
        if st and st.get("closed_pct", 0) > 0.5:
            flags.append({
                "type": "seller_closed_pattern",
                "category": "B",
                "score": 15,
                "title": "Sotuvchi yopiq auksion ishlatadi",
                "desc": f"Sotuvchining {st['closed_pct']*100:.0f}% lotlari yopiq auksionda.",
            })

    seller_total = (seller_stats or {}).get(lot.get("seller_id"), {}).get("total", 0)
    if seller_total >= 1000:
        flags.append({
            "type": "monopoly_seller",
            "category": "B",
            "score": 30,
            "title": "Monopoliyalashgan sotuvchi",
            "desc": f"Sotuvchida {seller_total} ta lot — mutlaq hukmron.",
        })
    elif seller_total >= 300:
        flags.append({
            "type": "dominant_seller",
            "category": "B",
            "score": 18,
            "title": "Hukmron sotuvchi",
            "desc": f"Sotuvchida {seller_total} ta lot — sezilarli mavqe.",
        })

    # ───────── C. BID-RIGGING ─────────
    bid = lot.get("bidders_count")
    if bid is not None and bid <= 1:
        flags.append({
            "type": "single_bidder",
            "category": "C",
            "score": 25,
            "title": "1 ishtirokchi",
            "desc": "Auksionda yagona ishtirokchi — Fazekas CRI eng kuchli signali.",
        })

    times = lot.get("times_auctioned") or 0
    if times >= 15:
        flags.append({
            "type": "many_reauctions",
            "category": "C",
            "score": 35,
            "title": f"{int(times)} marta auksionga chiqarilgan",
            "desc": "Lot ko'p marta sotilmagan — sun'iy yuqori narx yoki kelishilgan g'olibni kutmoqda.",
        })
    elif times >= 8:
        flags.append({
            "type": "repeat_auction",
            "category": "C",
            "score": 22,
            "title": f"{int(times)} marta auksionga chiqarilgan",
            "desc": "Lot bir necha marta sotilmagan — shubhali takroriy auksion.",
        })
    elif times >= 5:
        flags.append({
            "type": "reauction",
            "category": "C",
            "score": 12,
            "title": f"{int(times)} marta auksionga chiqarilgan",
            "desc": "Bir necha marta sotilmagan lot.",
        })

    if lot.get("is_descending"):
        flags.append({
            "type": "descending_auction",
            "category": "C",
            "score": 10,
            "title": "Teskari auksion",
            "desc": "Narx tushib boruvchi auksion — kelishilgan g'olib uchun qulay.",
        })

    # Combo bonus: closed + single bidder
    if is_closed and bid is not None and bid <= 1:
        flags.append({
            "type": "combo_single_closed",
            "category": "C",
            "score": 20,
            "title": "Yopiq + 1 ishtirokchi (CRI)",
            "desc": "Fazekas CRI metodologiyasidagi eng kuchli combo signal.",
        })

    if lot.get("is_juridical_only"):
        flags.append({
            "type": "physical_only",
            "category": "C",
            "score": 12,
            "title": "Cheklangan ishtirokchi turi",
            "desc": "Faqat ma'lum tipdagi shaxslar qatnashishi mumkin — cheklangan raqobat.",
        })

    # ───────── D. FRAUD ─────────
    sp = lot.get("start_price")
    sld = lot.get("sold_price")
    appraised = lot.get("appraised_price")

    # Below appraisal — most reliable benchmark
    if appraised and sp and appraised > 0:
        ratio = sp / appraised
        if ratio < 0.3:
            flags.append({
                "type": "appraisal_severe",
                "category": "D",
                "score": 35,
                "title": f"Boshlang'ich narx baholangandan {(1-ratio)*100:.0f}% past",
                "desc": "Rasmiy baholangan narxdan keskin past — sun'iy undervaluation belgisi.",
            })
        elif ratio < 0.5:
            flags.append({
                "type": "below_appraisal",
                "category": "D",
                "score": 22,
                "title": f"Baholangan narxdan {(1-ratio)*100:.0f}% past",
                "desc": "Boshlang'ich narx rasmiy bahodan past.",
            })
        elif ratio < 0.7:
            flags.append({
                "type": "below_appraisal",
                "category": "D",
                "score": 12,
                "title": f"Baholangan narxdan {(1-ratio)*100:.0f}% past",
                "desc": "Boshlang'ich narx baholangan narxdan past.",
            })

    # Region median benchmark
    if sp and region_stats and lot.get("region") in region_stats:
        median = region_stats[lot["region"]].get("median") or region_stats[lot["region"]].get("median_start_price")
        if median and median > 0:
            if sp < median * 0.3:
                flags.append({
                    "type": "deeply_underpriced",
                    "category": "D",
                    "score": 22,
                    "title": "Hudud medianidan keskin past",
                    "desc": f"Boshlang'ich narx hudud medianidan {(1-sp/median)*100:.0f}% past.",
                })
            elif sp < median * 0.5:
                flags.append({
                    "type": "underpriced",
                    "category": "D",
                    "score": 14,
                    "title": "Hudud medianidan past",
                    "desc": f"Boshlang'ich narx hudud medianidan {(1-sp/median)*100:.0f}% past.",
                })

    # Deep discount on sale
    if sp and sld and sp > 0:
        discount = (sp - sld) / sp * 100
        if discount > 30:
            flags.append({
                "type": "deep_discount",
                "category": "D",
                "score": 20,
                "title": f"Sotuv narxi {discount:.0f}% past",
                "desc": "Lot boshlang'ich narxdan ancha past sotilgan.",
            })

    if (lot.get("installment_months") or 0) >= 60:
        flags.append({
            "type": "long_installment",
            "category": "D",
            "score": 8,
            "title": "Uzoq muddatli to'lov",
            "desc": f"To'lov {lot['installment_months']} oyga bo'lib berilgan.",
        })

    # Combo: stuck lot + dominant seller
    if times >= 8 and seller_total >= 300:
        flags.append({
            "type": "stuck_lot_pattern",
            "category": "D",
            "score": 10,
            "title": "Yopishgan lot + hukmron sotuvchi",
            "desc": "Takroriy auksion + hukmron sotuvchi — kelishuv ehtimoli yuqori.",
        })

    # ───────── PEP / Conflict-of-Interest layer (B-toifa kengayishi) ─────────
    seller_name = lot.get("seller_name")
    seller_address = lot.get("seller_address") or lot.get("address")
    pep_match = pep_registry.match(seller_name)
    if pep_match:
        if pep_match["match_type"] in ("exact", "alias"):
            flags.append({
                "type": "pep_seller",
                "category": "B",
                "score": 35,
                "title": f"PEP: {pep_match['pep_name']}",
                "desc": (
                    f"Sotuvchi siyosatchi/mansabdor sifatida ro'yxatga olingan. "
                    f"{pep_match.get('case_summary') or ''}"
                ).strip(),
                "pep": pep_match,
            })
        elif pep_match["match_type"] == "fuzzy":
            flags.append({
                "type": "pep_seller",
                "category": "B",
                "score": 28,
                "title": f"PEP fuzzy match: {pep_match['pep_name']}",
                "desc": (
                    f"Sotuvchi nomi PEP bilan {pep_match['similarity']*100:.0f}% mos. "
                    "Boshqa familiya bilan yashirin urinish bo'lishi mumkin."
                ),
                "pep": pep_match,
            })
        elif pep_match["match_type"] == "family_lastname":
            flags.append({
                "type": "pep_family_match",
                "category": "B",
                "score": 25,
                "title": f"PEP oila a'zosi: {pep_match['pep_name']} familiyasi",
                "desc": (
                    f"Sotuvchining familiyasi PEP shaxs bilan bir xil — "
                    "oilaga yaqin shaxs bo'lishi mumkin (FATF R12)."
                ),
                "pep": pep_match,
            })

    gov_type = pep_registry.is_government_address(seller_address)
    if gov_type:
        flags.append({
            "type": "government_address",
            "category": "B",
            "score": 20,
            "title": f"Davlat ofisi manzili: {gov_type}",
            "desc": (
                "Sotuvchining manzili davlat tashkilotiga to'g'ri keladi — "
                "insider self-dealing belgisi."
            ),
        })

    # Family cluster (3+ sellers with same last name)
    if seller_name and family_clusters:
        ln = last_name(seller_name)
        if ln in family_clusters:
            flags.append({
                "type": "family_cluster",
                "category": "B",
                "score": 15,
                "title": f"Familiya klasteri: {ln}",
                "desc": (
                    f"Bu familiya bilan bog'liq {len(family_clusters)} ta yoki "
                    "ko'proq sotuvchi mavjud — qarindoshlik tarmog'i ehtimoli."
                ),
            })

    # ───────── Attach provenance / explainability ─────────
    for f in flags:
        meta = SOURCE.get(f["type"])
        if meta:
            f["ref"] = meta.get("ref")
            f["ref_url"] = meta.get("url")
            f["formula"] = meta.get("formula")
            f["fields"] = meta.get("fields")
        f["weight"] = WEIGHT.get(f["type"], 1.0)
        f["weighted_score"] = round(f["score"] * f["weight"], 1)

    # ───────── Score computation ─────────
    weighted = sum(f["weighted_score"] for f in flags)
    score = min(100, weighted)
    level = "low" if score < 40 else ("medium" if score < 70 else "high")

    # Per-category sub-scores
    cat_scores = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0}
    for f in flags:
        cat = f.get("category", "A")
        cat_scores[cat] = cat_scores.get(cat, 0) + f["score"] * WEIGHT.get(f["type"], 1.0)
    cat_scores = {k: min(100, round(v, 1)) for k, v in cat_scores.items()}

    return {
        "score": round(score, 1),
        "level": level,
        "flags": flags,
        "categories": cat_scores,
    }


def compute_region_stats(lots: Iterable[dict]) -> dict:
    from collections import defaultdict
    import statistics
    by_region = defaultdict(list)
    for lot in lots:
        if lot.get("region") and lot.get("start_price"):
            by_region[lot["region"]].append(lot["start_price"])
    return {
        r: {"median": statistics.median(prices), "count": len(prices)}
        for r, prices in by_region.items()
        if len(prices) >= 3
    }


def compute_seller_stats(lots: Iterable[dict]) -> dict:
    from collections import defaultdict
    counts = defaultdict(lambda: {"total": 0, "closed": 0})
    for lot in lots:
        # Seller key — prefer numeric seller_id, fallback to seller_hint
        key = lot.get("seller_id") or lot.get("seller_hint")
        if key is None:
            continue
        counts[key]["total"] += 1
        if lot.get("auction_type") == "closed":
            counts[key]["closed"] += 1
    out = {}
    for k, v in counts.items():
        out[k] = {
            "total": v["total"],
            "closed_pct": v["closed"] / v["total"] if v["total"] else 0,
        }
    return out
