"""
Market-wide series served from yfinance (no Sectors credits):
price performance, macro snapshot, and per-emiten corporate-event reactions.
"""
import math
import threading
import time
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
    sym = symbol.strip().upper().replace(".JK", "")

    def build():
        tk = yf.Ticker(f"{sym}.JK")
        actions = tk.actions
        hist = tk.history(period="5y", auto_adjust=False)
        if actions is None or actions.empty or hist is None or hist.empty:
            return {"symbol": sym, "events": [], "source": "yfinance"}
        close = hist["Close"].dropna()
        close.index = close.index.tz_localize(None)
        actions.index = actions.index.tz_localize(None)

        events = []
        for ts, row in actions.sort_index(ascending=False).iterrows():
            div, split = row.get("Dividends", 0) or 0, row.get("Stock Splits", 0) or 0
            if div <= 0 and split <= 0:
                continue
            before = close[close.index < ts]
            on_after = close[close.index >= ts]
            if before.empty or on_after.empty:
                continue
            prev = before.iloc[-1]
            day0 = on_after.iloc[0]
            day5 = on_after.iloc[min(4, len(on_after) - 1)]
            ev = {
                "date": ts.strftime("%Y-%m-%d"),
                "type": "DIVIDEND" if div > 0 else "SPLIT",
                "price_before": _clean(prev, 0),
                # Ex-date reaction; for dividends the drop includes the dividend itself.
                "reaction_1d_pct": _clean((day0 / prev - 1) * 100),
                "reaction_5d_pct": _clean((day5 / prev - 1) * 100),
            }
            if div > 0:
                ev["amount"] = _clean(div, 2)
                ev["yield_pct"] = _clean(div / prev * 100)
            else:
                ev["ratio"] = _clean(split, 4)
            events.append(ev)
            if len(events) >= limit:
                break
        return {"symbol": sym, "events": events, "source": "yfinance"}

    return _cached(f"events:{sym}:{limit}", build)
