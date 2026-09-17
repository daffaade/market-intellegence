"""
peer_analysis.py — Peer Analysis & Derived Metrics (Model-P0)
Implements §4 (Peer Analysis) from logic-ml.md and §9 of implementation plan.
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
for _p in [str(_HERE), str(_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


def compute_peer_medians(ticker_snapshots: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    if not ticker_snapshots:
        return {}
    df      = pd.DataFrame(ticker_snapshots).T
    df      = df.apply(pd.to_numeric, errors="coerce")
    medians = df.median().to_dict()
    return {k: float(v) for k, v in medians.items() if not np.isnan(v)}


def build_ticker_snapshot(feature_df: pd.DataFrame) -> Dict[str, float]:
    if feature_df.empty:
        return {}
    last = feature_df.iloc[-1]
    snap: Dict[str, float] = {}
    for col in last.index:
        try:
            val = float(last[col])
            if not np.isnan(val) and not np.isinf(val):
                snap[col] = val
        except (TypeError, ValueError):
            pass
    return snap


def peer_relative_position(
    ticker_snap: Dict[str, float],
    peer_medians: Dict[str, float],
    metrics: Optional[List[str]] = None,
) -> Dict[str, Dict[str, Any]]:
    if metrics is None:
        metrics = [
            "growth_proxy", "valuation_proxy",
            "institutional_flow", "forecast_proxy", "vol_20d",
        ]
    result: Dict[str, Dict[str, Any]] = {}
    for m in metrics:
        tv = ticker_snap.get(m)
        pm = peer_medians.get(m)
        if tv is None or pm is None:
            continue
        diff = tv - pm
        pos  = "Outperform" if diff > 0 else ("Underperform" if diff < 0 else "Neutral")
        result[m] = {
            "ticker_val":  round(tv, 6),
            "peer_median": round(pm, 6),
            "diff":        round(diff, 6),
            "position":    pos,
        }
    return result


def has_recent_dividend(fundamentals: Dict[str, Any]) -> bool:
    div = fundamentals.get("dividend", {})
    if not div or "_error" in div:
        return False
    if isinstance(div, dict):
        records = div.get("records", [])
        if isinstance(records, list) and len(records) > 0:
            return True
        if div.get("year"):
            return True
    return False
