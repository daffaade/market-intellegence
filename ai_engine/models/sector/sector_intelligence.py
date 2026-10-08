"""
Sector intelligence: relative strength, breadth and rotation for IDX sectors.

All constituents are downloaded in one batch (dividend-adjusted closes, 1 year)
together with IHSG. Per sector:
  - median 20- and 60-session return relative to IHSG
  - breadth: share of constituents above their 50-session average
  - rotation: change in the sector's 20-session relative-strength rank versus
    20 sessions ago (rising / falling / stable)
  - an equal-weight sector index (weekly, rebased) for charts

Replaces an implementation whose momentum score could never reach its ±0.5
thresholds (every sector was "Neutral"), whose sector names did not match the
backend's, and whose rotation signal was hard-coded.
"""
from __future__ import annotations

import math
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import yaml

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "sector_map.yaml"
_cache: Dict[str, Any] = {}
_lock = threading.Lock()


def load_sector_map() -> Dict[str, Any]:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _closes(symbols: List[str]) -> pd.DataFrame:
    with _lock:
        hit = _cache.get("closes")
        if hit and time.time() - hit[0] < 6 * 3600:
            return hit[1]
    import yfinance as yf
    tickers = [f"{s}.JK" for s in symbols] + ["^JKSE"]
    raw = yf.download(" ".join(tickers), period="1y", progress=False, auto_adjust=True)
    close = raw["Close"]
    close.index = pd.to_datetime(close.index).tz_localize(None)
    close = close.rename(columns=lambda c: c.replace(".JK", ""))
    with _lock:
        _cache["closes"] = (time.time(), close)
    return close


def _clean(v: Optional[float], nd: int = 4) -> Optional[float]:
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return None
    return round(float(v), nd)


def sector_overview(sector_map: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    cfg = sector_map or load_sector_map()
    sectors = cfg.get("sectors", {})
    th = cfg.get("thresholds", {})
    all_symbols = sorted({s for v in sectors.values() for s in v.get("symbols", [])})
    close = _closes(all_symbols)
    if "^JKSE" not in close or close["^JKSE"].dropna().empty:
        raise RuntimeError("IHSG history unavailable")
    ihsg = close["^JKSE"].ffill()

    def rel_return(series: pd.Series, n: int, end_offset: int = 0) -> Optional[float]:
        s = series.dropna()
        b = ihsg.reindex(s.index).ffill()
        if len(s) <= n + end_offset:
            return None
        e = len(s) - 1 - end_offset
        return float(s.iloc[e] / s.iloc[e - n] - 1) - float(b.iloc[e] / b.iloc[e - n] - 1)

    rows = []
    for key, spec in sectors.items():
        members = []
        for sym in spec.get("symbols", []):
            if sym not in close:
                continue
            s = close[sym].dropna()
            if len(s) < 70:
                continue
            ma50 = s.rolling(50).mean().iloc[-1]
            members.append({
                "symbol": sym,
                "rs_20d": rel_return(s, 20),
                "rs_60d": rel_return(s, 60),
                "rs_20d_prev": rel_return(s, 20, end_offset=20),
                "above_ma50": bool(s.iloc[-1] > ma50),
                "return_20d": float(s.iloc[-1] / s.iloc[-21] - 1),
            })
        if len(members) < th.get("min_constituents", 3):
            continue
        med = lambda k: float(np.median([m[k] for m in members if m[k] is not None]))
        rs20, rs60, rs20_prev = med("rs_20d"), med("rs_60d"), med("rs_20d_prev")
        breadth = sum(m["above_ma50"] for m in members) / len(members)
        if rs20 > th.get("rs_bullish", 0.02) and breadth >= th.get("breadth_bullish", 0.6):
            sentiment = "Bullish"
        elif rs20 < th.get("rs_bearish", -0.02) and breadth <= th.get("breadth_bearish", 0.4):
            sentiment = "Bearish"
        else:
            sentiment = "Neutral"

        # Equal-weight sector index, weekly, rebased to 100 over the last 26 weeks.
        idx = close[[m["symbol"] for m in members]].pct_change().mean(axis=1).fillna(0)
        level = (1 + idx).cumprod().resample("W-FRI").last().tail(27)
        level = level / level.iloc[0] * 100

        members.sort(key=lambda m: m["rs_20d"] if m["rs_20d"] is not None else float("-inf"), reverse=True)
        rows.append({
            "sector": key,
            "label": spec.get("label", key),
            "n_constituents": len(members),
            "sentiment": sentiment,
            "rs_20d": _clean(rs20),
            "rs_60d": _clean(rs60),
            "rs_20d_prev": _clean(rs20_prev),
            "breadth_ma50": _clean(breadth, 3),
            "constituents": [{**m, "rs_20d": _clean(m["rs_20d"]), "rs_60d": _clean(m["rs_60d"]),
                              "rs_20d_prev": _clean(m["rs_20d_prev"]), "return_20d": _clean(m["return_20d"])}
                             for m in members],
            "index_weekly": [{"date": d.strftime("%Y-%m-%d"), "value": _clean(v, 2)} for d, v in level.items()],
        })

    # Rotation: rank by 20-session relative strength now vs 20 sessions ago.
    def by(field):  # missing values rank last; 0.0 is a real value, not missing
        return lambda r: r[field] if r[field] is not None else float("-inf")

    now_rank = {r["sector"]: i + 1 for i, r in enumerate(sorted(rows, key=by("rs_20d"), reverse=True))}
    prev_rank = {r["sector"]: i + 1 for i, r in enumerate(sorted(rows, key=by("rs_20d_prev"), reverse=True))}
    for r in rows:
        r["rank"], r["rank_prev"] = now_rank[r["sector"]], prev_rank[r["sector"]]
        moved = r["rank_prev"] - r["rank"]
        r["rotation"] = "Menguat" if moved >= 2 else ("Melemah" if moved <= -2 else "Stabil")
    rows.sort(key=lambda r: r["rank"])

    last = close.index[-1]
    return {
        "as_of": last.strftime("%Y-%m-%d"),
        "benchmark": "IHSG",
        "method": "Median return 20/60 sesi vs IHSG, breadth di atas MA50, rotasi = perubahan peringkat 20 sesi",
        "sectors": rows,
        "source": "yfinance",
    }


class SectorIntelligenceModel:
    """Kept for callers that ask for one sector."""

    def __init__(self, data_loader=None):
        self.data_loader = data_loader

    def analyze_sector(self, sector_name: str, as_of: Optional[str] = None) -> Dict[str, Any]:
        overview = sector_overview()
        for row in overview["sectors"]:
            if row["sector"].lower() == sector_name.lower() or row["label"].lower() == sector_name.lower():
                return {**row, "as_of": overview["as_of"]}
        return {"sector": sector_name, "as_of": overview["as_of"], "error": "unknown sector"}
