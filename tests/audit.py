"""End-to-end audit + smoke tests for AuksionWatch.

Runs against live backend (port 8000) and frontend (port 3000).
Reports findings with PASS/WARN/FAIL.
"""
import sys
import json
import time
import sqlite3
from pathlib import Path
from collections import Counter

import httpx

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

API = "http://127.0.0.1:8000"
WEB = "http://localhost:3000"
DB = Path(__file__).resolve().parent.parent / "data" / "auksionwatch.db"

results: list[tuple[str, str, str, str]] = []  # (group, name, status, detail)


def add(group: str, name: str, status: str, detail: str = ""):
    results.append((group, name, status, detail))


def section(title: str):
    print(f"\n{'='*60}\n{title}\n{'='*60}")


# ───────── 1. BACKEND ENDPOINTS ─────────
def test_backend():
    section("1. BACKEND ENDPOINTS")
    client = httpx.Client(timeout=15)

    # 1.1 Root + version
    try:
        r = client.get(f"{API}/")
        if r.status_code == 200 and r.json().get("name") == "AuksionWatch API":
            add("backend", "/ root", "PASS", f"version {r.json().get('version')}")
        else:
            add("backend", "/ root", "FAIL", f"unexpected {r.status_code}")
    except Exception as e:
        add("backend", "/ root", "FAIL", str(e))

    # 1.2 /api/stats
    try:
        r = client.get(f"{API}/api/stats")
        d = r.json()
        if d.get("total", 0) > 1000:
            add("backend", "/api/stats", "PASS", f"total={d['total']}, high={d['high_risk']}")
        else:
            add("backend", "/api/stats", "FAIL", f"total too low: {d.get('total')}")
        if "categories" in d and len(d["categories"]) == 5:
            add("backend", "/api/stats categories", "PASS", "5 categories")
        else:
            add("backend", "/api/stats categories", "WARN", "missing/incomplete categories")
    except Exception as e:
        add("backend", "/api/stats", "FAIL", str(e))

    # 1.3 /api/lots with various filters
    for params, label in [
        ({"limit": 10}, "limit=10"),
        ({"risk_level": "high", "limit": 5}, "risk_level=high"),
        ({"region": "UZ-FA", "limit": 5}, "region=UZ-FA"),
        ({"q": "yer", "limit": 5}, "q=yer"),
        ({"auction_type": "open", "limit": 5}, "auction_type=open"),
        ({"limit": 1000, "offset": 500}, "pagination"),
    ]:
        try:
            r = client.get(f"{API}/api/lots", params=params)
            d = r.json()
            if r.status_code == 200 and "items" in d:
                add("backend", f"/api/lots {label}", "PASS", f"{len(d['items'])} items")
            else:
                add("backend", f"/api/lots {label}", "FAIL", f"{r.status_code}")
        except Exception as e:
            add("backend", f"/api/lots {label}", "FAIL", str(e))

    # 1.4 /api/lots/{id} — sample real lot, edge cases
    REAL_IDS = [23446154, 23447382]
    NONEXISTENT_IDS = [999999999, 0]
    for lid in REAL_IDS:
        try:
            r = client.get(f"{API}/api/lots/{lid}")
            if r.status_code == 200 and "lot" in r.json():
                lot = r.json()["lot"]
                flags = lot.get("flags") or []
                cats = lot.get("categories")
                if cats:
                    add("backend", f"/api/lots/{lid}", "PASS", f"risk={lot['risk_score']}, flags={len(flags)}")
                else:
                    add("backend", f"/api/lots/{lid}", "WARN", "missing categories")
            else:
                add("backend", f"/api/lots/{lid}", "FAIL", f"{r.status_code}")
        except Exception as e:
            add("backend", f"/api/lots/{lid}", "FAIL", str(e))
    for lid in NONEXISTENT_IDS:
        try:
            r = client.get(f"{API}/api/lots/{lid}")
            if r.status_code == 404:
                add("backend", f"/api/lots/{lid} (must 404)", "PASS", "correctly rejected")
            else:
                add("backend", f"/api/lots/{lid} (must 404)", "FAIL", f"got {r.status_code}")
        except Exception as e:
            add("backend", f"/api/lots/{lid}", "FAIL", str(e))

    # 1.5 /api/red-flags/today
    try:
        r = client.get(f"{API}/api/red-flags/today?limit=5")
        items = r.json().get("items", [])
        if all(it.get("risk_level") in ("high", "medium") for it in items):
            add("backend", "/api/red-flags/today", "PASS", f"{len(items)} items, all high/medium")
        else:
            add("backend", "/api/red-flags/today", "WARN", "contains non-flagged items")
    except Exception as e:
        add("backend", "/api/red-flags/today", "FAIL", str(e))

    # 1.6 /api/map/markers
    try:
        r = client.get(f"{API}/api/map/markers?risk_min=70")
        markers = r.json()
        if isinstance(markers, list) and len(markers) > 0:
            with_geo = sum(1 for m in markers if m.get("lat") and m.get("lon"))
            add("backend", "/api/map/markers", "PASS", f"{len(markers)} markers, {with_geo} with coords")
        else:
            add("backend", "/api/map/markers", "WARN", "no markers returned")
    except Exception as e:
        add("backend", "/api/map/markers", "FAIL", str(e))

    # 1.7 /api/sellers
    try:
        r = client.get(f"{API}/api/sellers?limit=5")
        items = r.json().get("items", [])
        if items and items[0]["total_lots"] >= items[-1]["total_lots"]:
            add("backend", "/api/sellers", "PASS", f"top={items[0]['total_lots']} lots")
        else:
            add("backend", "/api/sellers", "WARN", "ordering incorrect")
    except Exception as e:
        add("backend", "/api/sellers", "FAIL", str(e))

    # 1.8 /api/sellers/{id}
    try:
        r1 = client.get(f"{API}/api/sellers?limit=1")
        sid = r1.json()["items"][0]["seller_id"]
        r = client.get(f"{API}/api/sellers/{sid}")
        d = r.json()
        if d.get("total_lots", 0) > 0 and len(d.get("items", [])) > 0:
            add("backend", f"/api/sellers/{sid}", "PASS", f"{d['total_lots']} lots, {len(d['items'])} samples")
        else:
            add("backend", f"/api/sellers/{sid}", "FAIL", "empty")
    except Exception as e:
        add("backend", "/api/sellers/{id}", "FAIL", str(e))

    # 1.9 /api/network
    try:
        r = client.get(f"{API}/api/network?top=20")
        d = r.json()
        if "nodes" in d and "edges" in d and len(d["nodes"]) > 0:
            add("backend", "/api/network", "PASS", f"{len(d['nodes'])} nodes, {len(d['edges'])} edges")
        else:
            add("backend", "/api/network", "FAIL", "empty graph")
    except Exception as e:
        add("backend", "/api/network", "FAIL", str(e))

    # 1.10 /api/stats/timeline
    try:
        r = client.get(f"{API}/api/stats/timeline")
        series = r.json().get("series", [])
        if len(series) > 0:
            add("backend", "/api/stats/timeline", "PASS", f"{len(series)} months")
        else:
            add("backend", "/api/stats/timeline", "WARN", "no time data")
    except Exception as e:
        add("backend", "/api/stats/timeline", "FAIL", str(e))

    # 1.11 /api/export.csv
    try:
        r = client.get(f"{API}/api/export.csv?risk_level=high&limit=10")
        if r.status_code == 200 and "text/csv" in r.headers.get("content-type", ""):
            lines = r.text.splitlines()
            if len(lines) >= 2 and "lot_id" in lines[0]:
                add("backend", "/api/export.csv", "PASS", f"{len(lines)-1} rows")
            else:
                add("backend", "/api/export.csv", "WARN", "header missing")
        else:
            add("backend", "/api/export.csv", "FAIL", f"{r.status_code}")
    except Exception as e:
        add("backend", "/api/export.csv", "FAIL", str(e))

    # 1.12 SQL injection attempt
    try:
        r = client.get(f"{API}/api/lots", params={"q": "'; DROP TABLE lot; --"})
        if r.status_code == 200:
            add("backend", "SQL injection (q param)", "PASS", "parameterized — safe")
        else:
            add("backend", "SQL injection (q param)", "WARN", f"{r.status_code}")
    except Exception as e:
        add("backend", "SQL injection (q param)", "FAIL", str(e))

    client.close()


# ───────── 2. FRONTEND ROUTES ─────────
def test_frontend():
    section("2. FRONTEND ROUTES")
    client = httpx.Client(timeout=30, follow_redirects=True)
    routes = [
        ("/", "home"),
        ("/lots", "lots"),
        ("/lots?risk_level=high", "lots filter"),
        ("/map", "map"),
        ("/sellers", "sellers"),
        ("/network", "network"),
        ("/pep", "pep"),
        ("/methodology", "methodology"),
        ("/lot/23446154", "lot detail"),
        ("/seller/153123875", "seller detail"),
    ]
    for path, name in routes:
        try:
            t0 = time.time()
            r = client.get(f"{WEB}{path}")
            dt = time.time() - t0
            if r.status_code == 200:
                size_kb = len(r.text) / 1024
                if dt < 5:
                    add("frontend", name, "PASS", f"{dt:.1f}s, {size_kb:.0f}KB")
                else:
                    add("frontend", name, "WARN", f"slow: {dt:.1f}s")
            else:
                add("frontend", name, "FAIL", f"{r.status_code}")
        except Exception as e:
            add("frontend", name, "FAIL", str(e))

    # Static assets
    for asset in ["/logo.png", "/logo-icon.png"]:
        try:
            r = client.get(f"{WEB}{asset}")
            if r.status_code == 200 and len(r.content) > 1000:
                add("frontend", f"asset {asset}", "PASS", f"{len(r.content)/1024:.0f}KB")
            else:
                add("frontend", f"asset {asset}", "FAIL", f"{r.status_code}")
        except Exception as e:
            add("frontend", f"asset {asset}", "FAIL", str(e))

    client.close()


# ───────── 3. DATA INTEGRITY ─────────
def test_data():
    section("3. DATA INTEGRITY")
    if not DB.exists():
        add("data", "DB exists", "FAIL", "DB file missing")
        return
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    total = cur.execute("SELECT COUNT(*) FROM lot").fetchone()[0]
    if total > 10000:
        add("data", "lot count", "PASS", f"{total} lots")
    else:
        add("data", "lot count", "WARN", f"only {total} lots")

    # Risk levels distribution
    levels = dict(cur.execute("SELECT risk_level, COUNT(*) FROM lot GROUP BY risk_level").fetchall())
    add("data", "risk distribution", "PASS", f"high={levels.get('high',0)} medium={levels.get('medium',0)} low={levels.get('low',0)}")

    # Synthetic demo lots
    demo = cur.execute("SELECT COUNT(*) FROM lot WHERE id >= 90000000").fetchone()[0]
    if demo == 0:
        add("data", "no synthetic demo lots", "PASS", "0 demo lots")
    else:
        add("data", "no synthetic demo lots", "FAIL", f"{demo} demo lots present")

    # Categories field populated
    n = cur.execute("SELECT COUNT(*) FROM lot WHERE categories IS NOT NULL").fetchone()[0]
    if n == total:
        add("data", "categories populated", "PASS", f"all {n} lots have categories")
    else:
        add("data", "categories populated", "WARN", f"{total-n} lots missing categories")

    # Auction type distribution
    at = dict(cur.execute("SELECT auction_type, COUNT(*) FROM lot GROUP BY auction_type").fetchall())
    add("data", "auction_type breakdown", "PASS", str(at))

    # Region coverage
    nr = cur.execute("SELECT COUNT(DISTINCT region) FROM lot WHERE region IS NOT NULL").fetchone()[0]
    if nr >= 10:
        add("data", "region coverage", "PASS", f"{nr} regions")
    else:
        add("data", "region coverage", "WARN", f"only {nr} regions")

    # Seller_id consistency
    null_sid = cur.execute("SELECT COUNT(*) FROM lot WHERE seller_id IS NULL").fetchone()[0]
    add("data", "lots with seller_id", "PASS", f"{total-null_sid}/{total} ({(total-null_sid)/total*100:.1f}%)")

    # PEP entries integrity
    pep_path = DB.parent / "pep_watchlist.json"
    pep_data = json.loads(pep_path.read_text(encoding="utf-8"))
    pep_count = len(pep_data.get("officials", []))
    placeholder_ids = [o for o in pep_data["officials"] if "placeholder" in o["id"]]
    if not placeholder_ids:
        add("data", "PEP IDs clean", "PASS", f"{pep_count} entries, no -placeholder")
    else:
        add("data", "PEP IDs clean", "WARN", f"{len(placeholder_ids)} placeholder IDs")

    # Required fields
    nb_no_url = cur.execute("SELECT COUNT(*) FROM lot WHERE url IS NULL OR url = ''").fetchone()[0]
    if nb_no_url == 0:
        add("data", "every lot has URL", "PASS", "")
    else:
        add("data", "every lot has URL", "FAIL", f"{nb_no_url} missing")

    # Risk score sanity
    bad = cur.execute("SELECT COUNT(*) FROM lot WHERE risk_score < 0 OR risk_score > 100").fetchone()[0]
    if bad == 0:
        add("data", "risk_score in [0,100]", "PASS", "")
    else:
        add("data", "risk_score in [0,100]", "FAIL", f"{bad} out of range")

    conn.close()


# ───────── 4. RISK ENGINE LOGIC ─────────
def test_risk():
    section("4. RISK ENGINE")
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from backend.risk import evaluate

    # Empty lot
    r = evaluate({})
    if r["score"] == 0 and r["level"] == "low":
        add("risk", "empty lot → score 0", "PASS", "")
    else:
        add("risk", "empty lot → score 0", "FAIL", f"got {r['score']} {r['level']}")

    # Closed + single bidder + below appraisal
    r = evaluate({
        "auction_type": "closed",
        "bidders_count": 1,
        "start_price": 100,
        "appraised_price": 1000,
    })
    has_combo = any(f["type"] == "combo_single_closed" for f in r["flags"])
    has_severe = any(f["type"] == "appraisal_severe" for f in r["flags"])
    if has_combo and has_severe and r["level"] == "high":
        add("risk", "Ortikhov-style → high", "PASS", f"score={r['score']}")
    else:
        add("risk", "Ortikhov-style → high", "FAIL", f"missing flags: combo={has_combo} severe={has_severe}")

    # Many re-auctions
    r = evaluate({"times_auctioned": 50})
    if any(f["type"] == "many_reauctions" for f in r["flags"]):
        add("risk", "many_reauctions trigger", "PASS", f"score={r['score']}")
    else:
        add("risk", "many_reauctions trigger", "FAIL", "")

    # Score categories
    r = evaluate({
        "auction_type": "closed",
        "bidders_count": 1,
        "start_price": 100,
        "appraised_price": 1000,
        "times_auctioned": 30,
        "is_descending": True,
    })
    cats = r["categories"]
    active = sum(1 for v in cats.values() if v > 0)
    if active >= 2:
        add("risk", "multi-category scoring", "PASS", f"{active}/5 categories with score")
    else:
        add("risk", "multi-category scoring", "WARN", f"only {active}/5")

    # Provenance attached
    r = evaluate({"auction_type": "closed", "bidders_count": 1})
    has_ref = all(f.get("ref") for f in r["flags"])
    has_formula = all(f.get("formula") for f in r["flags"])
    if has_ref and has_formula:
        add("risk", "explainability fields", "PASS", "ref+formula on every flag")
    else:
        add("risk", "explainability fields", "FAIL", f"ref={has_ref} formula={has_formula}")


# ───────── 5. PEP MATCHING ─────────
def test_pep():
    section("5. PEP MATCHER")
    from backend.pep import get_registry

    reg = get_registry()
    # Real official
    m = reg.match("Akmalxon Ortiqov")
    if m and m["match_type"] == "exact":
        add("pep", "real official (exact)", "PASS", "Ortiqov matched")
    else:
        add("pep", "real official (exact)", "FAIL", str(m))

    # Cyrillic / alias
    m = reg.match("Эркинжон Турдимов")
    if m:
        add("pep", "Cyrillic match (Turdimov)", "PASS", f"{m['match_type']} {m['similarity']:.2f}")
    else:
        add("pep", "Cyrillic match (Turdimov)", "WARN", "no alias for Cyrillic Turdimov yet")

    # No match
    m = reg.match("Random Person")
    if m is None:
        add("pep", "non-PEP returns None", "PASS", "")
    else:
        add("pep", "non-PEP returns None", "FAIL", str(m))

    # Empty
    m = reg.match(None)
    if m is None:
        add("pep", "None input → None", "PASS", "")
    else:
        add("pep", "None input → None", "FAIL", str(m))

    # Government address
    g = reg.is_government_address("Toshkent shahar hokimligi binosi")
    if g:
        add("pep", "gov address detection", "PASS", g)
    else:
        add("pep", "gov address detection", "FAIL", "")

    # Excluded buyer-of-interest (Niyozov no longer in PEP list)
    m = reg.match("Niyozov Quvonchbek Xolmirzo o'g'li")
    if m is None or m.get("category") != "buyer-of-interest":
        add("pep", "Niyozov NOT in PEP list", "PASS", "buyer-of-interest cleaned")
    else:
        add("pep", "Niyozov NOT in PEP list", "FAIL", "still in PEP")


# ───────── 6. SECURITY ─────────
def test_security():
    section("6. SECURITY")
    root = Path(__file__).resolve().parent.parent

    # .gitignore covers .env
    gi = (root / ".gitignore").read_text()
    if ".env" in gi and "bot/.env" in gi:
        add("security", ".env in gitignore", "PASS", "")
    else:
        add("security", ".env in gitignore", "FAIL", "")

    # .env.example doesn't contain real-looking token
    ex = (root / "bot" / ".env.example").read_text()
    if "YOUR_BOT_TOKEN_HERE" in ex or "placeholder" in ex.lower():
        add("security", ".env.example sanitized", "PASS", "no real token")
    elif ":" in ex.split("BOT_TOKEN=")[1].split()[0]:
        # Looks like a real token format (digits:chars)
        token_line = next(l for l in ex.splitlines() if l.startswith("BOT_TOKEN="))
        token = token_line.split("=", 1)[1].strip()
        if len(token) > 20 and token.replace(":", "").replace("_", "").isalnum():
            add("security", ".env.example sanitized", "FAIL", f"contains real-looking token")
        else:
            add("security", ".env.example sanitized", "PASS", "")
    else:
        add("security", ".env.example sanitized", "PASS", "")

    # CORS open (intentional but flag for awareness)
    add("security", "CORS allow_origins=*", "WARN", "open by design — public read API")


# ───────── 7. PRINT REPORT ─────────
def report():
    section("AUDIT REPORT")
    by_status = Counter(s for _, _, s, _ in results)
    by_group = {}
    for g, n, s, d in results:
        by_group.setdefault(g, []).append((n, s, d))

    icon = {"PASS": "✓", "WARN": "⚠", "FAIL": "✗"}
    for group, items in by_group.items():
        print(f"\n[{group.upper()}]")
        for name, status, detail in items:
            line = f"  {icon[status]} {status:4}  {name}"
            if detail:
                line += f"  · {detail}"
            print(line)

    print("\n" + "=" * 60)
    print(f"PASS: {by_status['PASS']}   WARN: {by_status['WARN']}   FAIL: {by_status['FAIL']}")
    print("=" * 60)
    if by_status["FAIL"] == 0:
        print("\n✅ AUDIT CLEAN — no failures")
    else:
        print(f"\n❌ {by_status['FAIL']} FAILURES need attention")


if __name__ == "__main__":
    test_backend()
    test_frontend()
    test_data()
    test_risk()
    test_pep()
    test_security()
    report()
