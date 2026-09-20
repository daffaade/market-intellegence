"""
what_changed.py — Self-contained What Changed Fundamental Shift Detection (ai_engine)
Detects and ranks significant shifts in valuation, growth, margins, and financial metrics.
"""

from __future__ import annotations
import math
from typing import Any, Dict, List, Optional, Union


def safe_divide(numerator: Any, denominator: Any) -> Optional[float]:
    if numerator is None or denominator is None:
        return None
    try:
        num = float(numerator)
        den = float(denominator)
        if den == 0.0 or math.isnan(den) or math.isnan(num):
            return None
        return num / den
    except (TypeError, ValueError, ZeroDivisionError):
        return None


METRIC_CATEGORIES = [
    "valuation_metrics",
    "growth_metrics",
    "price_metrics",
    "ownership_metrics",
    "dividend_metrics"
]


def compute_what_changed(
    metrics_now: Dict[str, Any],
    metrics_prev: Dict[str, Any],
    threshold_pct: float = 10.0,
    sort_by: str = "magnitude"
) -> Dict[str, Any]:
    """
    Computes significant metric shifts between two periods.
    """
    if not isinstance(metrics_now, dict) or not isinstance(metrics_prev, dict):
        return {
            "status": "ERROR",
            "error": "metrics_now and metrics_prev must be dictionaries"
        }

    changes: List[Dict[str, Any]] = []

    for category in METRIC_CATEGORIES:
        cat_now = metrics_now.get(category, {})
        cat_prev = metrics_prev.get(category, {})

        if not isinstance(cat_now, dict) or not isinstance(cat_prev, dict):
            continue

        for field, value_now in cat_now.items():
            value_prev = cat_prev.get(field)
            if value_now is None or value_prev is None:
                continue

            try:
                v_now = float(value_now)
                v_prev = float(value_prev)
            except (ValueError, TypeError):
                continue

            delta = v_now - v_prev
            if abs(v_prev) > 1e-9:
                d_pct = safe_divide(delta, abs(v_prev))
                delta_pct = (d_pct * 100.0) if d_pct is not None else 0.0
            else:
                delta_pct = 100.0 if delta > 0 else (-100.0 if delta < 0 else 0.0)

            if abs(delta_pct) >= threshold_pct:
                changes.append({
                    "category": category,
                    "field": field,
                    "value_before": round(v_prev, 4),
                    "value_after": round(v_now, 4),
                    "delta": round(delta, 4),
                    "delta_pct": round(delta_pct, 2),
                    "direction": "increase" if delta > 0 else "decrease"
                })

    if sort_by == "delta_pct":
        changes.sort(key=lambda x: x["delta_pct"], reverse=True)
    else:
        changes.sort(key=lambda x: abs(x["delta_pct"]), reverse=True)

    return {
        "status": "SUCCESS",
        "changes": changes,
        "total_changes_detected": len(changes)
    }


class WhatChangedModel:
    def __init__(self, data_loader=None):
        self.data_loader = data_loader

    def analyze(self, symbol: str) -> Dict[str, Any]:
        """
        Analyzes fundamental shifts for symbol.
        """
        # Snapshot sample context
        now_snap = {
            "valuation_metrics": {"pe": 18.5, "pbv": 2.1},
            "growth_metrics": {"revenue_growth_yoy": 12.4, "net_income_growth_yoy": 15.2},
            "ownership_metrics": {"foreign_flow_pct": 5.4}
        }
        prev_snap = {
            "valuation_metrics": {"pe": 21.0, "pbv": 2.4},
            "growth_metrics": {"revenue_growth_yoy": 8.1, "net_income_growth_yoy": 9.5},
            "ownership_metrics": {"foreign_flow_pct": 2.1}
        }

        diff = compute_what_changed(now_snap, prev_snap)
        return {
            "status": "success",
            "symbol": symbol,
            "significant_changes": diff.get("changes", []),
            "total_changes": diff.get("total_changes_detected", 0)
        }
