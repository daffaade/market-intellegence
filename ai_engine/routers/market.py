"""
Market-wide series served from yfinance (no Sectors credits):
price performance, macro snapshot, and per-emiten corporate-event reactions.
"""
import math
import threading
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List

import pandas as pd
import yfinance as yf
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/v1", tags=["market"])

_TTL_SECONDS = 6 * 3600
_cache: Dict[str, Any] = {}
_lock = threading.Lock()


def _cached(key: str, build: Callable[[], Any]) -> Any:
    with _lock:
        hit = _cache.get(key)
        if hit and time.time() - hit[0] < _TTL_SECONDS:
            return hit[1]
    value = build()
    with _lock:
        _cache[key] = (time.time(), value)
    return value


def _closes(tickers: List[str], period: str) -> pd.DataFrame:
    data = yf.download(" ".join(tickers), period=period, progress=False, auto_adjust=True, group_by="column")
    if data is None or data.empty:
        return pd.DataFrame()
    close = data["Close"]
    if isinstance(close, pd.Series):
        close = close.to_frame(name=tickers[0])
    return close


def _clean(v: Any, nd: int = 2):
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) or math.isinf(f) else round(f, nd)


# ---------------------------------------------------------------------
# Price performance (weekly closes, 1 year)
# ---------------------------------------------------------------------

@router.get("/market/performance")
def market_performance(symbols: str = Query(..., description="Comma-separated IDX symbols")):
    syms = sorted({s.strip().upper().replace(".JK", "") for s in symbols.split(",") if s.strip()})
    if not syms or len(syms) > 30:
        raise HTTPException(status_code=400, detail="provide 1-30 symbols")

    def build():
        close = _closes([f"{s}.JK" for s in syms], "1y")
        if close.empty:
            raise HTTPException(status_code=502, detail="price history unavailable")
        weekly = close.resample("W-FRI").last().dropna(how="all")
        points = []
        for ts, row in weekly.iterrows():
            point = {"date": ts.strftime("%Y-%m-%d")}
            for s in syms:
                point[s] = _clean(row.get(f"{s}.JK"))
            points.append(point)
        return {"symbols": syms, "points": points, "source": "yfinance", "as_of": points[-1]["date"] if points else None}

    return _cached("perf:" + ",".join(syms), build)


# ---------------------------------------------------------------------
# Macro snapshot
# ---------------------------------------------------------------------

_MACRO = [
    {"key": "jkse", "ticker": "^JKSE", "name": "IHSG", "unit": "poin"},
    {"key": "usdidr", "ticker": "IDR=X", "name": "USD/IDR", "unit": "rupiah"},
    {"key": "brent", "ticker": "BZ=F", "name": "Minyak Brent", "unit": "USD/barel"},
    {"key": "gold", "ticker": "GC=F", "name": "Emas", "unit": "USD/troy oz"},
]


def _pct(series: pd.Series, days: int):
    if series.empty:
        return None
    end_date = series.index[-1]
    past = series[series.index <= end_date - pd.Timedelta(days=days)]
    if past.empty:
        return None
    return _clean((series.iloc[-1] / past.iloc[-1] - 1) * 100)


@router.get("/macro/snapshot")
def macro_snapshot():
    def build():
        close = _closes([m["ticker"] for m in _MACRO], "1y")
        if close.empty:
            raise HTTPException(status_code=502, detail="macro series unavailable")
        out = []
        for m in _MACRO:
            if m["ticker"] not in close:
                continue
            s = close[m["ticker"]].dropna()
            if s.empty:
                continue
            spark = s.resample("W-FRI").last().dropna().tail(26)
            out.append({
                "key": m["key"],
                "name": m["name"],
                "unit": m["unit"],
                "value": _clean(s.iloc[-1]),
                "date": s.index[-1].strftime("%Y-%m-%d"),
                "change_1m_pct": _pct(s, 30),
                "change_1y_pct": _pct(s, 365),
                "sparkline": [_clean(v) for v in spark.tolist()],
            })
        return {"indicators": out, "source": "yfinance"}

    return _cached("macro", build)


# ---------------------------------------------------------------------
# Corporate events (dividends & splits) with price reaction
# ---------------------------------------------------------------------

@router.get("/events/{symbol}")
def corporate_events(symbol: str, limit: int = 8):
    """
    Dividends and splits with an event study per event: abnormal return vs IHSG
    from a market model estimated on the 250..30 sessions before the event,
    cumulated over [-1, +5], with a t-test. Prices are dividend-adjusted, so the
    mechanical ex-date drop is not counted as a reaction.
    """
    sym = symbol.strip().upper().replace(".JK", "")

    def build():
        from ai_engine.models.event_study.event_study import _compute_event, _load_config
        tk = yf.Ticker(f"{sym}.JK")
        actions = tk.actions
        if actions is None or actions.empty:
            return {"symbol": sym, "events": [], "source": "yfinance"}
        actions.index = pd.to_datetime(actions.index).tz_localize(None)
        closes = _closes([f"{sym}.JK", "^JKSE"], "5y")
        closes.index = pd.to_datetime(closes.index).tz_localize(None)
        stock_ret = closes[f"{sym}.JK"].pct_change().dropna()
        mkt_ret = closes["^JKSE"].pct_change().dropna()
        # Unadjusted closes for the dividend yield (adjusted ones understate the price).
        raw_hist = tk.history(period="5y", auto_adjust=False)
        raw_close = raw_hist["Close"].dropna() if raw_hist is not None and not raw_hist.empty else closes[f"{sym}.JK"]
        raw_close.index = pd.to_datetime(raw_close.index).tz_localize(None)
        cfg = dict(_load_config())
        cfg["event_window"] = {"start": -1, "end": 5}

        events = []
        for ts, row in actions.sort_index(ascending=False).iterrows():
            div, split = row.get("Dividends", 0) or 0, row.get("Stock Splits", 0) or 0
            if div <= 0 and split <= 0:
                continue
            kind = "DIVIDEND" if div > 0 else "SPLIT"
            date = ts.strftime("%Y-%m-%d")
            res = _compute_event({"ticker": sym, "date": date, "event_type": kind.lower()}, stock_ret, mkt_ret, cfg)
            if res.get("car") is None:
                continue
            before = raw_close[raw_close.index < ts]
            ev = {
                "date": date,
                "type": kind,
                "car_pct": _clean(res["car"] * 100),
                "t_stat": _clean(res["t_stat"]),
                "p_value": _clean(res["p_value"], 4),
                "significant": bool(res["significant_at_5pct"]),
                "beta": _clean(res["beta"], 3),
                "window": "[-1, +5]",
                "data_quality": res.get("data_quality"),
            }
            if div > 0:
                ev["amount"] = _clean(div, 2)
                if not before.empty:
                    ev["yield_pct"] = _clean(div / float(before.iloc[-1]) * 100)
            else:
                ev["ratio"] = _clean(split, 4)
            events.append(ev)
            if len(events) >= limit:
                break
        return {"symbol": sym, "events": events, "method": "event study, model pasar vs IHSG", "source": "yfinance"}

    return _cached(f"events2:{sym}:{limit}", build)


@router.get("/macro/sensitivity/{symbol}")
def macro_sensitivity(symbol: str):
    """Weekly-return betas of the stock on IHSG, USD/IDR, Brent and gold (2 years)."""
    from ai_engine.models.macro_impact.macro_impact import run_macro_impact
    sym = symbol.strip().upper().replace(".JK", "")
    return _cached(f"macro_sens:{sym}", lambda: run_macro_impact(sym))


@router.get("/pipeline/sources")
def pipeline_sources():
    """Where each kind of data comes from and how fresh the local cache is."""
    import json as _json
    from pathlib import Path
    from data_processing.data_sectors import fundamentals as F, market_series as M

    def scan(folder: Path, pattern: str, ttl: int):
        stamps = []
        for f in folder.glob(pattern):
            try:
                stamps.append(float(_json.loads(f.read_text(encoding="utf-8")).get("fetched_at", 0)))
            except (OSError, ValueError):
                continue
        if not stamps:
            return {"items": 0, "newest": None, "oldest": None, "ttl_hours": ttl // 3600}
        iso = lambda t: datetime.fromtimestamp(t, tz=timezone.utc).isoformat()
        return {"items": len(stamps), "newest": iso(max(stamps)), "oldest": iso(min(stamps)), "ttl_hours": ttl // 3600}

    return {"sources": [
        {"key": "sectors_report", "label": "Laporan perusahaan", "provider": "Sectors",
         "used_for": "Fundamental, valuasi vs peer, kepemilikan, dividen, perubahan tahunan",
         **scan(F.REPORT_CACHE_DIR, "*.json", F.REPORT_TTL_SECONDS)},
        {"key": "sectors_foreign_flow", "label": "Arus asing harian", "provider": "Sectors",
         "used_for": "Faktor arus asing, smart money, katalis",
         **scan(M.CACHE_DIR, "foreign_flow_*.json", M.FOREIGN_FLOW_TTL)},
        {"key": "sectors_ihsg", "label": "IHSG harian", "provider": "Sectors",
         "used_for": "Pembanding kinerja relatif",
         **scan(M.CACHE_DIR, "index_ihsg.json", M.INDEX_TTL)},
        {"key": "yfinance_prices", "label": "Riwayat harga panjang & makro", "provider": "Yahoo Finance",
         "used_for": "Model prediksi, volatilitas, MA200, anomali, sensitivitas makro, USD/IDR, Brent, emas",
         "items": None, "newest": None, "oldest": None, "ttl_hours": 6},
    ]}
