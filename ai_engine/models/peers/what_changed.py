from __future__ import annotations
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

CURRENT_DIR = Path(__file__).resolve().parent
AI_ENGINE_DIR = CURRENT_DIR.parent.parent
REPO_ROOT = AI_ENGINE_DIR.parent
for _p in [str(CURRENT_DIR), str(AI_ENGINE_DIR), str(REPO_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from ai_engine.core.derived_metrics import (
        safe_divide,
        fetch_and_compute_derived_metrics,
        compute_derived_metrics,
        _get
    )
    HAS_DERIVED_METRICS = True
except ImportError:
    try:
        from core.derived_metrics import (
            safe_divide,
            fetch_and_compute_derived_metrics,
            compute_derived_metrics,
            _get
        )
        HAS_DERIVED_METRICS = True
    except ImportError:
        HAS_DERIVED_METRICS = False

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

        def _get(obj: Any, path: str, default: Any = None) -> Any:
            if obj is None:
                return default
            parts = path.split(".")
            curr = obj
            for part in parts:
                if curr is None:
                    return default
                if isinstance(curr, dict):
                    curr = curr.get(part, default)
                elif hasattr(curr, part):
                    curr = getattr(curr, part, default)
                else:
                    return default
            return curr if curr is not None else default


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
        Analyzes fundamental shifts for symbol across reporting periods using derived metrics.
        """
        clean_sym = symbol.upper().replace(".JK", "").strip()

        # Initialize snapshots dynamically (no hardcoded mock metrics)
        now_snap: Dict[str, Any] = {}
        prev_snap: Dict[str, Any] = {}

        # Dynamic computation using derived metrics when available
        if HAS_DERIVED_METRICS:
            try:
                live_now = fetch_and_compute_derived_metrics(clean_sym, period="current")
                live_prev = fetch_and_compute_derived_metrics(clean_sym, period="1y")

                if isinstance(live_now, dict) and any(cat in live_now for cat in METRIC_CATEGORIES):
                    for cat in METRIC_CATEGORIES:
                        if cat in live_now and isinstance(live_now[cat], dict):
                            now_snap.setdefault(cat, {}).update({
                                k: v for k, v in live_now[cat].items() if v is not None
                            })

                if isinstance(live_prev, dict) and any(cat in live_prev for cat in METRIC_CATEGORIES):
                    for cat in METRIC_CATEGORIES:
                        if cat in live_prev and isinstance(live_prev[cat], dict):
                            prev_snap.setdefault(cat, {}).update({
                                k: v for k, v in live_prev[cat].items() if v is not None
                            })
            except Exception:
                pass

        diff = compute_what_changed(now_snap, prev_snap)
        return {
            "status": "success",
            "symbol": clean_sym,
            "significant_changes": diff.get("changes", []),
            "total_changes": diff.get("total_changes_detected", 0)
        }
