"""
Company fundamentals from the full Sectors `/company/report/{symbol}/` payload.

The normalised pipeline (caching.py) keeps only the first row of each list,
which is enough for scoring but not for the dashboard (multi-year financials,
all shareholders, all executives). This module keeps the raw report on disk
for 7 days, so each symbol costs at most one Sectors credit per week, and maps
it to the shape the Go backend serves as CompanyFundamentals.
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# A full report costs 8 Sectors credits (1 per section), so it is kept 14 days;
# fundamentals change quarterly. Only tracked symbols are ever refetched.
REPORT_TTL_SECONDS = 14 * 24 * 3600
REPORT_CACHE_DIR = Path(__file__).resolve().parent / ".cache" / "reports"


def _report_path(symbol: str) -> Path:
    return REPORT_CACHE_DIR / f"{symbol}.json"


def save_report(symbol: str, report: Dict[str, Any]) -> None:
    """Persist a raw report so later fundamentals requests reuse it."""
    if not report:
        return
    REPORT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"fetched_at": time.time(), "report": report}
    tmp = _report_path(symbol).with_suffix(".tmp")
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    tmp.replace(_report_path(symbol))


def load_report(symbol: str, max_age: int = REPORT_TTL_SECONDS) -> Optional[Dict[str, Any]]:
    """Return {"fetched_at", "report"} if a cached report exists and is fresh enough."""
    path = _report_path(symbol)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if time.time() - payload.get("fetched_at", 0) > max_age:
        return None
    return payload


def get_report(symbol: str, miner=None) -> Optional[Dict[str, Any]]:
    """Cached report, or one fresh Sectors call (1 credit) when the cache is cold."""
    symbol = symbol.replace(".JK", "").upper()
    cached = load_report(symbol)
    if cached:
        return cached
    if miner is None:
        from data_processing.data_sectors.dataminer import SectorsDataMiner
        miner = SectorsDataMiner()
    report = miner.mine_company_report(symbol)  # also persisted via save_report
    if not report:
        return None
    return load_report(symbol) or {"fetched_at": time.time(), "report": report}


# ---------------------------------------------------------------------
# Mapping
# ---------------------------------------------------------------------

def _num(v: Any) -> Optional[float]:
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def _r(v: Optional[float], nd: int = 2) -> Optional[float]:
    return round(v, nd) if v is not None else None


def map_growth(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = (report.get("financials") or {}).get("historical_financials") or []
    out = []
    for row in sorted(rows, key=lambda r: str(r.get("year"))):
        revenue, earnings = _num(row.get("revenue")), _num(row.get("earnings"))
        if revenue is None and earnings is None:
            continue
        margin = (earnings / revenue * 100) if revenue and earnings is not None else None
        out.append({
            "year": str(row.get("year")),
            "revenue": _r(revenue / 1e9 if revenue is not None else 0, 1),   # billions IDR
            "net_profit": _r(earnings / 1e9 if earnings is not None else 0, 1),
            "margin": _r(margin, 1) if margin is not None else 0,
        })
    return out


def map_dividends(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    hist = (report.get("dividend") or {}).get("historical_dividends") or {}
    eps = (report.get("financials") or {}).get("historical_eps") or {}
    out = []
    for year in sorted(hist):
        d = hist[year] or {}
        dps = _num(d.get("total_dividend"))
        if dps is None:
            continue
        y_eps = _num((eps.get(year) or {}).get("eps"))
        # Dividends are paid out of the previous year's profit.
        p_eps = _num((eps.get(str(int(year) - 1)) or {}).get("eps")) if year.isdigit() else None
        base = p_eps or y_eps
        payout = dps / base * 100 if base else None
        # Sectors does not split-adjust old DPS (e.g. BBCA's 2021 split), which
        # shows up as an impossible payout; report it as unknown instead.
        if payout is not None and not 0 < payout <= 150:
            payout = None
        out.append({
            "year": str(year),
            "dividend_per_share": _r(dps, 1),
            "yield_percent": _r((_num(d.get("total_yield")) or 0) * 100, 2),
            "payout_ratio": _r(payout, 1),
        })
    return out


def _holder_category(name: str) -> str:
    n = name.lower()
    if "treasury" in n or "saham treasuri" in n:
        return "TREASURY"
    if n in ("public", "masyarakat", "publik") or "public" in n or "masyarakat" in n:
        return "RETAIL"
    if "negara" in n or "republic of indonesia" in n or "republik indonesia" in n or "danantara" in n:
        return "GOVERNMENT"
    return "INSTITUTIONAL"


def map_shareholders(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = (report.get("ownership") or {}).get("major_shareholders") or []
    exec_names = {
        (e.get("name") or "").strip().lower()
        for e in ((report.get("management") or {}).get("executives_shareholdings") or [])
    }
    out = []
    for row in rows:
        name = (row.get("name") or "").strip()
        pct = _num(row.get("share_percentage"))
        if not name or pct is None:
            continue
        category = "MANAGEMENT" if name.lower() in exec_names else _holder_category(name)
        out.append({"name": name, "share_percentage": _r(pct * 100, 2), "category": category})
    out.sort(key=lambda r: r["share_percentage"], reverse=True)
    return out


def map_executives(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    mgmt = report.get("management") or {}
    holdings = {
        (h.get("name") or "").strip().lower(): h
        for h in (mgmt.get("executives_shareholdings") or [])
    }
    out = []
    for e in mgmt.get("key_executives") or []:
        name = (e.get("name") or "").strip()
        if not name:
            continue
        h = holdings.get(name.lower()) or {}
        amount = _num(h.get("share_amount"))
        pct = _num(h.get("share_percentage"))
        out.append({
            "name": name,
            "position": e.get("position") or "",
            "share_amount": int(amount) if amount is not None else None,
            "share_percentage": _r(pct * 100, 5) if pct is not None else None,
        })
    return out


def map_smart_money(report: Dict[str, Any]) -> Dict[str, Any]:
    own = report.get("ownership") or {}
    top = own.get("top_transactions") or {}

    def side(rows, action):
        return [
            {"institution": r.get("name") or "", "action": action,
             "shares_change": int(_num(r.get("changeAmount")) or 0)}
            for r in rows or [] if r.get("name")
        ]

    flow = [
        {"date": r.get("date"), "net_shares": int(_num(r.get("net_transaction")) or 0)}
        for r in own.get("institutional_transaction_flow") or [] if r.get("date")
    ]
    flow.sort(key=lambda r: r["date"])
    return {
        "as_of": top.get("date"),
        "transactions": side(top.get("top_buyers"), "ACCUMULATE") + side(top.get("top_sellers"), "DISTRIBUTE"),
        "monthly_flow": flow,
    }


def map_fundamentals(symbol: str, report: Dict[str, Any], fetched_at: float) -> Dict[str, Any]:
    smart = map_smart_money(report)
    return {
        "symbol": symbol,
        "growth_data": map_growth(report),
        "dividends": map_dividends(report),
        "shareholders": map_shareholders(report),
        "executives": map_executives(report),
        "smart_money": smart["transactions"],
        "smart_money_as_of": smart["as_of"],
        "institutional_flow": smart["monthly_flow"],
        "source": "sectors",
        "fetched_at": datetime.fromtimestamp(fetched_at, tz=timezone.utc).isoformat(),
    }
