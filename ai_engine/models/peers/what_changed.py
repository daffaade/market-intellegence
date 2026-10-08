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


def _num(v: Any) -> Optional[float]:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) or math.isinf(f) else f


def _by_year(rows: Any, key: str = "year") -> Dict[str, Dict[str, Any]]:
    if isinstance(rows, dict):
        rows = [dict(v, **{key: k}) for k, v in rows.items() if isinstance(v, dict)]
    return {str(r.get(key)): r for r in (rows or []) if isinstance(r, dict) and r.get(key) is not None}


def _id(text: str) -> str:
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


def changes_from_report(report: Dict[str, Any], threshold_pct: float = 10.0) -> List[Dict[str, Any]]:
    """
    Year-over-year changes from the Sectors company report: latest reported year
    vs the year before, for income, profitability, leverage, valuation and dividend.
    `favorable` says whether the move is good for the company (None = neutral).
    """
    fin = report.get("financials") or {}
    sector = ((report.get("overview") or {}).get("sector") or "").lower()
    is_bank = "financ" in sector or "bank" in sector
    out: List[Dict[str, Any]] = []

    def add(label, prev, curr, period, fmt, higher_is_better, absolute_pp=False):
        if prev is None or curr is None:
            return
        if absolute_pp:
            delta_pct = (curr - prev) * 100  # percentage points
            significant = abs(delta_pct) >= 1.0
            delta_text = _id(f"{delta_pct:+.1f}") + " poin"
        else:
            if abs(prev) < 1e-12:
                return
            delta_pct = (curr - prev) / abs(prev) * 100
            significant = abs(delta_pct) >= threshold_pct
            delta_text = _id(f"{delta_pct:+.1f}") + "%"
        if not significant:
            return
        favorable = None if higher_is_better is None else ((curr > prev) == higher_is_better)
        out.append({
            "metric": label,
            "period": period,
            "prior_value": prev,
            "current_value": curr,
            "prior_text": fmt(prev),
            "current_text": fmt(curr),
            "delta_pct": round(delta_pct, 2),
            "delta_text": delta_text,
            "shift_detected": True,
            "favorable": favorable,
        })

    trillion = lambda v: "Rp " + _id(f"{v / 1e12:,.1f}") + " T"
    pct = lambda v: _id(f"{v * 100:.1f}") + "%"
    times = lambda v: _id(f"{v:.1f}") + "x"

    fy = _by_year(fin.get("historical_financials"))
    years = sorted(fy)
    if len(years) >= 2:
        y0, y1 = years[-2], years[-1]
        per = f"{y0}→{y1}"
        add("Pendapatan", _num(fy[y0].get("revenue")), _num(fy[y1].get("revenue")), per, trillion, True)
        add("Laba bersih", _num(fy[y0].get("earnings")), _num(fy[y1].get("earnings")), per, trillion, True)

    ratios = _by_year(fin.get("historical_financial_ratio"))
    years = sorted(ratios)
    if len(years) >= 2:
        r0, r1 = ratios[years[-2]], ratios[years[-1]]
        per = f"{years[-2]}→{years[-1]}"
        prof0, prof1 = r0.get("profitability") or {}, r1.get("profitability") or {}
        add("ROE", _num(prof0.get("roe")), _num(prof1.get("roe")), per, pct, True, absolute_pp=True)
        add("Marjin laba bersih", _num(prof0.get("net_profit_margin")), _num(prof1.get("net_profit_margin")), per, pct, True, absolute_pp=True)
        if not is_bank:
            lev0, lev1 = r0.get("leverage") or {}, r1.get("leverage") or {}
            add("Utang terhadap ekuitas", _num(lev0.get("debt_to_equity_ratio")), _num(lev1.get("debt_to_equity_ratio")), per, times, False)

    hv = _by_year((report.get("valuation") or {}).get("historical_valuation"))
    years = sorted(hv)
    if len(years) >= 2:
        v0, v1 = hv[years[-2]], hv[years[-1]]
        per = f"{years[-2]}→{years[-1]}"
        # Valuation re-rating is neither good nor bad for the company itself.
        pe0, pe1 = _num(v0.get("pe")), _num(v1.get("pe"))
        # A PER from losses or near-zero profit is not a valuation; skip it.
        if pe0 and pe1 and 0 < pe0 <= 200 and 0 < pe1 <= 200:
            add("PER", pe0, pe1, per, times, None)
        add("PBV", _num(v0.get("pb")), _num(v1.get("pb")), per, times, None)

    divs = _by_year((report.get("dividend") or {}).get("historical_dividends"), key="year")
    years = sorted(y for y in divs if y.isdigit() and int(y) < __import__("datetime").date.today().year)
    if len(years) >= 2:
        rp = lambda v: "Rp " + _id(f"{v:,.1f}")
        add("Dividen per saham", _num(divs[years[-2]].get("total_dividend")), _num(divs[years[-1]].get("total_dividend")),
            f"{years[-2]}→{years[-1]}", rp, True)

    out.sort(key=lambda c: abs(c["delta_pct"]), reverse=True)
    return out


class WhatChangedModel:
    def __init__(self, data_loader=None):
        self.data_loader = data_loader

    def analyze(self, symbol: str) -> Dict[str, Any]:
        """
        Year-over-year shifts from the cached Sectors company report (no new fetch:
        the analysis pipeline keeps that cache warm). The earlier implementation
        compared two "periods" that the data layer resolved to the same snapshot,
        so it always reported no change.
        """
        clean_sym = symbol.upper().replace(".JK", "").strip()
        try:
            from data_processing.data_sectors.fundamentals import load_report
            cached = load_report(clean_sym, max_age=30 * 24 * 3600)
        except Exception:
            cached = None
        if not cached:
            return {"status": "success", "symbol": clean_sym, "significant_changes": [], "total_changes": 0,
                    "data_quality": "missing"}
        changes = changes_from_report(cached["report"])
        return {"status": "success", "symbol": clean_sym, "significant_changes": changes,
                "total_changes": len(changes), "source": "sectors"}
