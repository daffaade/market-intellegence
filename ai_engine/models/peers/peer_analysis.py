"""
peer_analysis.py — Self-contained Peer Comparison & Relative Positioning (ai_engine)
Computes peer medians, rankings, outperform/underperform positions, and divergence context.
"""

from __future__ import annotations
import math
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple

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


DEFAULT_PEERS_MAP = {
    "BBCA": ["BMRI", "BBRI", "BBNI"],
    "BMRI": ["BBCA", "BBRI", "BBNI"],
    "BBRI": ["BBCA", "BMRI", "BBNI"],
    "BBNI": ["BBCA", "BMRI", "BBRI"],
    "TLKM": ["ISAT", "EXCL"],
    "ISAT": ["TLKM", "EXCL"],
    "EXCL": ["TLKM", "ISAT"],
    "BUMI": ["ADRO", "PTBA", "ITMG"],
    "ADRO": ["PTBA", "ITMG", "BUMI"],
    "PTBA": ["ADRO", "ITMG", "BUMI"],
    "ICBP": ["INDF", "MYOR", "UNVR"],
    "INDF": ["ICBP", "MYOR"],
    "UNVR": ["ICBP", "MYOR", "KLBF"],
    "ASII": ["AUTO", "IMAS"]
}


def compute_peer_medians(ticker_snapshots: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    if not ticker_snapshots:
        return {}
    df = pd.DataFrame(ticker_snapshots).T
    df = df.apply(pd.to_numeric, errors="coerce")
    medians = df.median().to_dict()
    return {k: float(v) for k, v in medians.items() if not np.isnan(v)}


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
        pos = "Outperform" if diff > 0 else ("Underperform" if diff < 0 else "Neutral")
        result[m] = {
            "ticker_val": round(tv, 6),
            "peer_median": round(pm, 6),
            "diff": round(diff, 6),
            "position": pos,
        }
    return result


class PeerAnalysisModel:
    def __init__(self, data_loader=None):
        self.data_loader = data_loader

    def analyze(self, symbol: str) -> Dict[str, Any]:
        """
        Runs peer analysis and benchmark comparisons for the given symbol using derived metrics.
        """
        clean_sym = symbol.upper().replace(".JK", "").strip()
        peers = DEFAULT_PEERS_MAP.get(clean_sym, ["BMRI", "BBRI", "BBNI"])
        # Ensure target ticker itself is not in peer group
        peers = [p for p in peers if p != clean_sym]
        if not peers:
            peers = ["BMRI", "BBRI", "BBNI"]

        peers_context = {}
        valuation_context = {}

        if self.data_loader:
            try:
                p_res = self.data_loader.get_peers(clean_sym, "current")
                if isinstance(p_res, dict) and p_res.get("value"):
                    peers_context = p_res["value"]

                v_res = self.data_loader.get_valuation(clean_sym, "current")
                if isinstance(v_res, dict) and v_res.get("value"):
                    valuation_context = v_res["value"]
            except Exception:
                pass

        # Initialize snapshots dynamically (no hardcoded mock values)
        ticker_snap: Dict[str, float] = {
            "growth_proxy": 0.0,
            "valuation_proxy": 0.0,
            "institutional_flow": 0.0,
            "forecast_proxy": 0.0,
            "vol_20d": 0.0
        }
        peer_medians: Dict[str, float] = {
            "growth_proxy": 0.0,
            "valuation_proxy": 0.0,
            "institutional_flow": 0.0,
            "forecast_proxy": 0.0,
            "vol_20d": 0.0
        }

        # Dynamic computation using derived metrics when available
        if HAS_DERIVED_METRICS:
            try:
                target_m = fetch_and_compute_derived_metrics(clean_sym, period="current")
                if isinstance(target_m, dict):
                    val_m = target_m.get("valuation_metrics", {})
                    gro_m = target_m.get("growth_metrics", {})
                    pri_m = target_m.get("price_metrics", {})
                    own_m = target_m.get("ownership_metrics", {})

                    if gro_m.get("revenue_growth_yoy") is not None:
                        ticker_snap["growth_proxy"] = round(float(gro_m["revenue_growth_yoy"]) / 100.0, 4)
                    if val_m.get("pe_relative") is not None:
                        ticker_snap["valuation_proxy"] = round(float(val_m["pe_relative"]), 4)
                    if own_m.get("net_institutional_flow_pct") is not None:
                        ticker_snap["institutional_flow"] = round(float(own_m["net_institutional_flow_pct"]) / 100.0, 4)
                    if gro_m.get("forecast_gap") is not None:
                        ticker_snap["forecast_proxy"] = round(float(gro_m["forecast_gap"]) / 100.0, 4)
                    if pri_m.get("volatility") is not None:
                        ticker_snap["vol_20d"] = round(float(pri_m["volatility"]), 4)

                # Fetch peers derived metrics to calculate dynamic peer medians
                peer_snaps = {}
                for p_sym in peers:
                    p_m = fetch_and_compute_derived_metrics(p_sym, period="current")
                    if isinstance(p_m, dict):
                        p_val = p_m.get("valuation_metrics", {})
                        p_gro = p_m.get("growth_metrics", {})
                        p_pri = p_m.get("price_metrics", {})
                        p_own = p_m.get("ownership_metrics", {})
                        p_snap = {}
                        if p_gro.get("revenue_growth_yoy") is not None:
                            p_snap["growth_proxy"] = round(float(p_gro["revenue_growth_yoy"]) / 100.0, 4)
                        if p_val.get("pe_relative") is not None:
                            p_snap["valuation_proxy"] = round(float(p_val["pe_relative"]), 4)
                        if p_own.get("net_institutional_flow_pct") is not None:
                            p_snap["institutional_flow"] = round(float(p_own["net_institutional_flow_pct"]) / 100.0, 4)
                        if p_gro.get("forecast_gap") is not None:
                            p_snap["forecast_proxy"] = round(float(p_gro["forecast_gap"]) / 100.0, 4)
                        if p_pri.get("volatility") is not None:
                            p_snap["vol_20d"] = round(float(p_pri["volatility"]), 4)
                        if p_snap:
                            peer_snaps[p_sym] = p_snap

                if peer_snaps:
                    dyn_medians = compute_peer_medians(peer_snaps)
                    peer_medians.update(dyn_medians)
            except Exception:
                pass

        rel_positions = peer_relative_position(ticker_snap, peer_medians)

        # Dynamic divergence score calculation
        diff_vals = [abs(pos["diff"]) for pos in rel_positions.values() if "diff" in pos]
        if diff_vals:
            raw_score = sum(diff_vals) / len(diff_vals) * 10.0
            divergence_score = round(min(0.95, max(0.15, raw_score)), 2)
        else:
            divergence_score = 0.50

        # Dynamic insights generation
        insights = []
        for metric, pos_info in rel_positions.items():
            pos = pos_info.get("position")
            metric_label = metric.replace("_", " ")
            if pos == "Outperform":
                insights.append(f"{clean_sym} is outperforming peer median in {metric_label}")
            elif pos == "Underperform":
                insights.append(f"{clean_sym} is underperforming peer median in {metric_label}")

        if not insights:
            insights = [
                f"{clean_sym} metrics are within the peer group median range"
            ]

        return {
            "status": "success",
            "symbol": clean_sym,
            "peer_group": peers,
            "peers_context": peers_context or {"peers": peers},
            "valuation_context": valuation_context,
            "relative_positions": rel_positions,
            "divergence_score": divergence_score,
            "insights": insights
        }
