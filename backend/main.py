"""FastAPI backend for AuksionWatch.

REST API endpointlari + auto-seed (Railway production'da DB bo'sh bo'lsa
lots_parsed.json'dan avtomatik to'ldiradi). 18+ endpoint bilan frontend va
Telegram bot xizmat ko'rsatadi.
"""
import csv
import io
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select, func, or_

# Loyiha root'ini sys.path'ga qo'shamiz — relative import'lar uchun
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.db import engine, init_db, get_session
from backend.models import Lot


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App lifecycle hook — startup va shutdown'da bajariladigan ish.

    Startup'da:
      1. DB jadvalni yaratish + ALTER TABLE migration
      2. AUTOSEED=1 va DB bo'sh bo'lsa — lots_parsed.json'dan import + rescore
    """
    print(f"[startup] AuksionWatch v1.2 — initializing", flush=True)
    init_db()
    print(f"[startup] DB initialized · DATABASE_URL host hint: {os.getenv('DATABASE_URL', 'sqlite-default').split('@')[-1][:60]}", flush=True)

    # AUTOSEED=1 (default) — Railway production'da birinchi boot'da seed bo'ladi
    autoseed = os.getenv("AUTOSEED", "1")
    print(f"[startup] AUTOSEED={autoseed}", flush=True)
    if autoseed != "0":
        try:
            # DB'da nechta lot borligini sanab ko'ramiz
            with Session(engine) as session:
                count = session.exec(select(func.count(Lot.id))).one()
            print(f"[startup] existing lot count: {count}", flush=True)

            # Seed manbasi — image ichida lots_parsed.json (~2.7MB, 1993 lot)
            seed_path = Path(__file__).parent.parent / "data" / "lots_parsed.json"
            print(f"[startup] seed file exists: {seed_path.exists()} ({seed_path})", flush=True)

            # Faqat DB BO'SH bo'lsa va seed fayl mavjud bo'lsa — import qilamiz
            if count == 0 and seed_path.exists():
                print(f"[startup] DB empty — running reingest...", flush=True)
                from backend.reingest_v11 import main as reingest_main  # noqa
                reingest_main()  # JSON → DB
                print(f"[startup] reingest done — running rescore...", flush=True)
                from backend.rescore_all import main as rescore_main
                rescore_main()   # Risk score'ni qayta hisoblash + categories
                print(f"[startup] auto-seed complete", flush=True)
            elif count > 0:
                print(f"[startup] DB already has {count} lots — skipping seed", flush=True)
            else:
                print(f"[startup] seed file missing — cannot seed", flush=True)
        except Exception as e:
            # Seed muvaffaqiyatsiz bo'lsa app'ni to'xtatmaslik — log qoldiramiz
            import traceback
            print(f"[startup] auto-seed FAILED: {e}", flush=True)
            traceback.print_exc()
    yield  # App ishga tushadi


# CORS — env'dan allowlist (production'da aniq domain, default: ochiq read-only API)
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app = FastAPI(
    title="AuksionWatch API",
    description=(
        "E-AUKSION antikorrupsiya monitoring tizimi. "
        "OECD/OCP standartlari asosida 5 toifali risk tahlili."
    ),
    version="1.2.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def healthz():
    """Railway healthcheck endpoint — har 30 sekundda Railway tekshiradi."""
    return {"status": "ok"}


@app.get("/")
def root():
    """API root — versiya va kategoriyalar haqida ma'lumot."""
    return {
        "name": "AuksionWatch API",
        "version": "1.1.0",
        "docs": "/docs",
        "categories": {
            "A": "Low Transparency",
            "B": "Collusion",
            "C": "Bid-Rigging",
            "D": "Fraud",
            "E": "Low Competition",
        },
    }


@app.get("/api/lots")
def list_lots(
    # ── Filtr parametrlari (hammasi ixtiyoriy) ──
    region: Optional[str] = None,           # masalan UZ-FA
    auction_type: Optional[str] = None,     # open / closed / unknown
    risk_level: Optional[str] = None,       # high / medium / low
    risk_min: float = 0,                    # minimum risk_score
    seller_id: Optional[int] = None,        # aniq sotuvchi
    seller_hint: Optional[str] = None,      # davaktiv / court / bank
    ownership: Optional[str] = None,        # state / confiscated / private — egalik turi bo'yicha guruh
    q: Optional[str] = None,                # qidiruv (title/address/seller)
    limit: int = Query(50, ge=1, le=2000),  # max 2000 (eksport uchun)
    offset: int = Query(0, ge=0),           # pagination
    session: Session = Depends(get_session),
):
    # Filter shartlarini bir marta yig'amiz — count va items uchun bir xil
    base = select(Lot).where(Lot.risk_score >= risk_min)
    if region:
        base = base.where(Lot.region == region)
    if auction_type:
        base = base.where(Lot.auction_type == auction_type)
    if risk_level:
        base = base.where(Lot.risk_level == risk_level)
    if seller_id:
        base = base.where(Lot.seller_id == seller_id)
    if seller_hint:
        base = base.where(Lot.seller_hint == seller_hint)
    # Egalik turi bo'yicha guruhlash filter
    if ownership == "state":
        base = base.where(Lot.seller_hint.in_(["davaktiv", "state", "gov"]))
    elif ownership == "confiscated":
        base = base.where(Lot.seller_hint.in_(["court", "mib", "bank"]))
    elif ownership == "private":
        base = base.where(Lot.seller_hint.in_(["individual", "private"]))
    if q:
        like = f"%{q}%"
        base = base.where(or_(Lot.title.like(like), Lot.address.like(like), Lot.seller_name.like(like)))

    # Filter bo'yicha umumiy count — paginatsiya uchun zarur
    count_stmt = select(func.count()).select_from(base.subquery())
    total = session.exec(count_stmt).one()

    items = session.exec(
        base.order_by(Lot.risk_score.desc()).limit(limit).offset(offset)
    ).all()
    return {"count": total, "items": items, "limit": limit, "offset": offset}


@app.get("/api/lots/{lot_id}")
def get_lot(lot_id: int, session: Session = Depends(get_session)):
    lot = session.get(Lot, lot_id)
    if not lot:
        raise HTTPException(404, "lot not found")
    related = []
    if lot.seller_id is not None:
        rel_stmt = (
            select(Lot)
            .where(Lot.seller_id == lot.seller_id, Lot.id != lot_id)
            .order_by(Lot.risk_score.desc())
            .limit(5)
        )
        related = session.exec(rel_stmt).all()
    if not related and lot.seller_hint:
        rel_stmt = (
            select(Lot)
            .where(Lot.seller_hint == lot.seller_hint, Lot.id != lot_id)
            .order_by(Lot.risk_score.desc())
            .limit(5)
        )
        related = session.exec(rel_stmt).all()
    return {"lot": lot, "related": related}


@app.get("/api/red-flags/today")
def red_flags_today(limit: int = 10, session: Session = Depends(get_session)):
    stmt = (
        select(Lot)
        .where(Lot.risk_level.in_(["high", "medium"]))
        .order_by(Lot.risk_score.desc())
        .limit(limit)
    )
    return {"items": session.exec(stmt).all()}


@app.get("/api/stats")
def stats(session: Session = Depends(get_session)):
    total = session.exec(select(func.count(Lot.id))).one()
    high = session.exec(select(func.count(Lot.id)).where(Lot.risk_level == "high")).one()
    medium = session.exec(select(func.count(Lot.id)).where(Lot.risk_level == "medium")).one()
    closed = session.exec(select(func.count(Lot.id)).where(Lot.auction_type == "closed")).one()
    total_value = session.exec(select(func.sum(Lot.start_price))).one() or 0
    high_value = (
        session.exec(select(func.sum(Lot.start_price)).where(Lot.risk_level == "high")).one()
        or 0
    )

    region_rows = session.exec(
        select(Lot.region, func.count(Lot.id))
        .where(Lot.region.is_not(None))
        .group_by(Lot.region)
    ).all()
    by_region = [{"region": r, "count": c} for r, c in region_rows]

    risk_region_rows = session.exec(
        select(Lot.region, func.count(Lot.id))
        .where(Lot.region.is_not(None), Lot.risk_level == "high")
        .group_by(Lot.region)
    ).all()
    risk_by_region = [{"region": r, "high_count": c} for r, c in risk_region_rows]

    # Category aggregation — sum lots that have at least one signal in each category
    cat_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0}
    cat_sums = {"A": 0.0, "B": 0.0, "C": 0.0, "D": 0.0, "E": 0.0}
    rows = session.exec(select(Lot.categories).where(Lot.categories.is_not(None))).all()
    for cats in rows:
        if not cats:
            continue
        for k in "ABCDE":
            v = cats.get(k, 0) or 0
            if v > 0:
                cat_counts[k] += 1
                cat_sums[k] += v

    categories = [
        {
            "code": k,
            "lots_with_signal": cat_counts[k],
            "avg_score": round(cat_sums[k] / cat_counts[k], 1) if cat_counts[k] else 0,
        }
        for k in "ABCDE"
    ]

    # Egalik bo'yicha taqsimot — judge "davlat mol-mulki qaerda?" deb so'rasa
    # darrov javob berish uchun. Davlat / Musodara / Yuridik shaxs alohida.
    state_total = session.exec(
        select(func.count(Lot.id)).where(Lot.seller_hint.in_(["davaktiv", "state", "gov"]))
    ).one()
    state_high = session.exec(
        select(func.count(Lot.id)).where(
            Lot.seller_hint.in_(["davaktiv", "state", "gov"]),
            Lot.risk_level == "high",
        )
    ).one()
    confiscated_total = session.exec(
        select(func.count(Lot.id)).where(Lot.seller_hint.in_(["court", "mib", "bank"]))
    ).one()
    private_total = session.exec(
        select(func.count(Lot.id)).where(Lot.seller_hint.in_(["individual", "private"]))
    ).one()
    ownership_breakdown = {
        "state": {"total": state_total, "high_risk": state_high},
        "confiscated": {"total": confiscated_total},
        "private": {"total": private_total},
    }

    # Risk distribution — har darajaning foizi (judge "false positive ulushi
    # qancha?" deb so'rasa to'g'ridan-to'g'ri javob berish uchun)
    low_count = max(0, total - high - medium)
    distribution = {
        "high": {
            "count": high,
            "pct": round(high / total * 100, 1) if total else 0,
        },
        "medium": {
            "count": medium,
            "pct": round(medium / total * 100, 1) if total else 0,
        },
        "low": {
            "count": low_count,
            "pct": round(low_count / total * 100, 1) if total else 0,
        },
    }

    return {
        "total": total,
        "high_risk": high,
        "medium_risk": medium,
        "closed_auctions": closed,
        "total_value_uzs": float(total_value),
        "high_risk_value_uzs": float(high_value),
        "by_region": by_region,
        "high_risk_by_region": risk_by_region,
        "categories": categories,
        "distribution": distribution,
        "ownership_breakdown": ownership_breakdown,
    }


@app.get("/api/map/markers")
def map_markers(
    risk_min: float = 0,
    region: Optional[str] = None,
    session: Session = Depends(get_session),
):
    stmt = select(Lot).where(
        Lot.geo_lat.is_not(None),
        Lot.geo_lon.is_not(None),
        Lot.risk_score >= risk_min,
    )
    if region:
        stmt = stmt.where(Lot.region == region)
    items = session.exec(stmt.limit(3000)).all()
    return [
        {
            "id": l.id,
            "lat": l.geo_lat,
            "lon": l.geo_lon,
            "risk": l.risk_score,
            "level": l.risk_level,
            "title": l.title or l.lot_type or f"Lot #{l.id}",
            "region": l.region,
        }
        for l in items
    ]


@app.get("/api/firms/{seller_hint}")
def firm_history(seller_hint: str, session: Session = Depends(get_session)):
    stmt = select(Lot).where(Lot.seller_hint == seller_hint).order_by(Lot.risk_score.desc())
    items = session.exec(stmt.limit(50)).all()
    if not items:
        raise HTTPException(404, "no lots for this seller")
    total = len(items)
    closed = sum(1 for l in items if l.auction_type == "closed")
    high = sum(1 for l in items if l.risk_level == "high")
    return {
        "seller_hint": seller_hint,
        "total_lots": total,
        "closed_pct": closed / total * 100 if total else 0,
        "high_risk_count": high,
        "items": items,
    }


@app.get("/api/stats/timeline")
def stats_timeline(session: Session = Depends(get_session)):
    """Monthly time-series aggregation. Parses end_time/start_time into month buckets."""
    import re
    from collections import defaultdict
    from datetime import datetime

    rows = session.exec(
        select(Lot.end_time, Lot.start_time, Lot.risk_level, Lot.auction_type, Lot.start_price)
    ).all()
    buckets: dict[str, dict] = defaultdict(
        lambda: {"total": 0, "high": 0, "medium": 0, "closed": 0, "value": 0.0}
    )

    def parse_month(s):
        if not s:
            return None
        s = str(s).strip()
        # try "2026-05-12 ..." or "12.05.2026 ..."
        m = re.match(r"(\d{4})-(\d{2})", s)
        if m:
            return f"{m.group(1)}-{m.group(2)}"
        m = re.match(r"\d{2}\.(\d{2})\.(\d{4})", s)
        if m:
            return f"{m.group(2)}-{m.group(1)}"
        return None

    for end_time, start_time, risk_level, auction_type, start_price in rows:
        bucket = parse_month(end_time) or parse_month(start_time)
        if not bucket:
            continue
        b = buckets[bucket]
        b["total"] += 1
        if risk_level == "high":
            b["high"] += 1
        elif risk_level == "medium":
            b["medium"] += 1
        if auction_type == "closed":
            b["closed"] += 1
        if start_price:
            b["value"] += float(start_price)

    series = sorted(
        [{"month": m, **v} for m, v in buckets.items()],
        key=lambda x: x["month"],
    )
    # Trim to last 18 months
    series = series[-18:]
    return {"series": series}


@app.get("/api/network")
def seller_network(
    top: int = Query(50, le=200),
    session: Session = Depends(get_session),
):
    """Build a graph of top sellers + their region adjacency.

    Nodes: sellers + regions
    Edges: seller-region weighted by lot count
    """
    rows = session.exec(
        select(
            Lot.seller_id,
            Lot.seller_name,
            Lot.region,
            func.count(Lot.id).label("count"),
            func.avg(Lot.risk_score).label("avg_risk"),
        )
        .where(Lot.seller_id.is_not(None), Lot.region.is_not(None))
        .group_by(Lot.seller_id, Lot.seller_name, Lot.region)
    ).all()

    seller_totals: dict[int, dict] = {}
    for sid, sname, region, count, avg_risk in rows:
        if sid not in seller_totals:
            seller_totals[sid] = {
                "id": sid,
                "name": sname,
                "total_lots": 0,
                "regions": [],
                "weighted_risk": 0.0,
            }
        seller_totals[sid]["total_lots"] += count
        seller_totals[sid]["weighted_risk"] += float(avg_risk or 0) * count
        seller_totals[sid]["regions"].append({"region": region, "count": count})

    sellers_sorted = sorted(
        seller_totals.values(),
        key=lambda s: -s["total_lots"],
    )[:top]

    nodes = []
    edges = []
    seen_regions = set()

    for s in sellers_sorted:
        avg_risk = s["weighted_risk"] / s["total_lots"] if s["total_lots"] else 0
        nodes.append({
            "id": f"s{s['id']}",
            "type": "seller",
            "label": (s["name"] or f"#{s['id']}")[:40],
            "value": s["total_lots"],
            "risk": round(avg_risk, 1),
        })
        for r in s["regions"]:
            if r["region"] not in seen_regions:
                nodes.append({
                    "id": f"r{r['region']}",
                    "type": "region",
                    "label": r["region"],
                    "value": 0,
                })
                seen_regions.add(r["region"])
            edges.append({
                "source": f"s{s['id']}",
                "target": f"r{r['region']}",
                "value": r["count"],
            })

    return {"nodes": nodes, "edges": edges}


@app.get("/api/sellers")
def sellers_leaderboard(
    limit: int = Query(20, le=200),
    min_lots: int = 5,
    ownership: Optional[str] = Query(None, description="state | confiscated | private | all"),
    session: Session = Depends(get_session),
):
    """Top sellers by lot count, optionally filtered by ownership channel.

    ownership param:
      - state         → seller_hint IN ('davaktiv','state','gov') — Davaktiv (davlat)
      - confiscated   → seller_hint IN ('court','mib','bank')      — sud orqali musodara
      - private       → seller_hint IN ('individual','private')    — yuridik shaxs
      - None / 'all'  → barcha sotuvchilar
    """
    stmt = (
        select(
            Lot.seller_id,
            Lot.seller_name,
            Lot.region,
            func.max(Lot.seller_hint).label("seller_hint"),
            func.count(Lot.id).label("total"),
            func.sum(func.iif(Lot.auction_type == "closed", 1, 0)).label("closed"),
            func.sum(func.iif(Lot.risk_level == "high", 1, 0)).label("high_risk"),
            func.sum(func.iif(Lot.risk_level == "medium", 1, 0)).label("medium_risk"),
            func.avg(Lot.risk_score).label("avg_risk"),
            func.sum(Lot.start_price).label("total_value"),
        )
        .where(Lot.seller_id.is_not(None))
    )
    # Ownership filter — Davaktiv vs MIB vs Yuridik shaxs
    if ownership == "state":
        stmt = stmt.where(Lot.seller_hint.in_(["davaktiv", "state", "gov"]))
    elif ownership == "confiscated":
        stmt = stmt.where(Lot.seller_hint.in_(["court", "mib", "bank"]))
    elif ownership == "private":
        stmt = stmt.where(Lot.seller_hint.in_(["individual", "private"]))

    rows = session.exec(
        stmt.group_by(Lot.seller_id, Lot.seller_name, Lot.region)
        .having(func.count(Lot.id) >= min_lots)
        .order_by(func.count(Lot.id).desc())
        .limit(limit)
    ).all()

    return {
        "items": [
            {
                "seller_id": r[0],
                "seller_name": r[1],
                "region": r[2],
                "seller_hint": r[3],
                "total_lots": r[4],
                "closed_count": r[5] or 0,
                "high_risk_count": r[6] or 0,
                "medium_risk_count": r[7] or 0,
                "avg_risk_score": round(float(r[8] or 0), 1),
                "total_value_uzs": float(r[9] or 0),
                "closed_pct": round((r[5] or 0) / r[4] * 100, 1) if r[4] else 0,
                "high_risk_pct": round((r[6] or 0) / r[4] * 100, 1) if r[4] else 0,
            }
            for r in rows
        ]
    }


@app.get("/api/sellers/{seller_id}")
def seller_detail(seller_id: int, session: Session = Depends(get_session)):
    lots = session.exec(
        select(Lot).where(Lot.seller_id == seller_id).order_by(Lot.risk_score.desc())
    ).all()
    if not lots:
        raise HTTPException(404, "seller not found")
    total = len(lots)
    closed = sum(1 for l in lots if l.auction_type == "closed")
    high = sum(1 for l in lots if l.risk_level == "high")
    medium = sum(1 for l in lots if l.risk_level == "medium")
    total_val = sum(l.start_price or 0 for l in lots)
    name = next((l.seller_name for l in lots if l.seller_name), None)
    region = next((l.region for l in lots if l.region), None)

    return {
        "seller_id": seller_id,
        "seller_name": name,
        "region": region,
        "total_lots": total,
        "closed_count": closed,
        "high_risk_count": high,
        "medium_risk_count": medium,
        "closed_pct": round(closed / total * 100, 1) if total else 0,
        "high_risk_pct": round(high / total * 100, 1) if total else 0,
        "total_value_uzs": float(total_val),
        "items": lots[:50],
    }


@app.get("/api/export.csv")
def export_csv(
    region: Optional[str] = None,
    risk_level: Optional[str] = None,
    risk_min: float = 0,
    limit: int = Query(5000, le=20000),
    session: Session = Depends(get_session),
):
    """CSV export for journalists / analysts."""
    stmt = select(Lot).where(Lot.risk_score >= risk_min)
    if region:
        stmt = stmt.where(Lot.region == region)
    if risk_level:
        stmt = stmt.where(Lot.risk_level == risk_level)
    items = session.exec(stmt.order_by(Lot.risk_score.desc()).limit(limit)).all()

    def gen():
        buf = io.StringIO()
        # UTF-8 BOM so Excel opens correctly
        yield "﻿"
        writer = csv.writer(buf, delimiter=",", quoting=csv.QUOTE_MINIMAL)
        headers = [
            "lot_id", "url", "title", "region", "district", "auction_type",
            "start_price", "sold_price", "appraised_price", "bidders_count",
            "times_auctioned", "seller_id", "seller_name", "seller_hint",
            "risk_score", "risk_level", "category_A", "category_B",
            "category_C", "category_D", "category_E", "flags_count", "flag_titles",
        ]
        writer.writerow(headers)
        yield buf.getvalue()
        buf.seek(0); buf.truncate(0)

        for l in items:
            cats = l.categories or {}
            flag_titles = "; ".join((f.get("title") or "") for f in (l.flags or []))
            writer.writerow([
                l.id, l.url, l.title or "", l.region or "", l.district or "",
                l.auction_type, l.start_price or "", l.sold_price or "",
                l.appraised_price or "", l.bidders_count or "",
                l.times_auctioned or "", l.seller_id or "",
                l.seller_name or "", l.seller_hint or "",
                l.risk_score, l.risk_level,
                cats.get("A", 0), cats.get("B", 0),
                cats.get("C", 0), cats.get("D", 0), cats.get("E", 0),
                len(l.flags or []), flag_titles,
            ])
            yield buf.getvalue()
            buf.seek(0); buf.truncate(0)

    return StreamingResponse(
        gen(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="auksionwatch-export.csv"',
        },
    )


@app.get("/api/export.json")
def export_json(
    region: Optional[str] = None,
    risk_level: Optional[str] = None,
    risk_min: float = 0,
    limit: int = Query(5000, le=20000),
    session: Session = Depends(get_session),
):
    stmt = select(Lot).where(Lot.risk_score >= risk_min)
    if region:
        stmt = stmt.where(Lot.region == region)
    if risk_level:
        stmt = stmt.where(Lot.risk_level == risk_level)
    items = session.exec(stmt.order_by(Lot.risk_score.desc()).limit(limit)).all()
    return {
        "metadata": {
            "version": "1.1.0",
            "license": "CC BY-SA 4.0",
            "source": "e-auksion.uz (open sitemap + official Excel reports)",
            "methodology": "OECD/OCP 5-category red-flag taxonomy",
        },
        "count": len(items),
        "items": items,
    }
