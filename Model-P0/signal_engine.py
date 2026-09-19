"""
signal_engine.py — Fundamental Divergence, Opportunity & Risk Signal (Model-P0)
Implements §9-§12 of implementation-plan-forecast-signal-module.md
and §5.7-§5.9 of logic-ml.md.  Scores 0-100, no recommendation language.
"""

import sys
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
for _p in [str(_HERE), str(_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ── Helper ────────────────────────────────────────────────────────────────────
def _mm(value: float, lo: float, hi: float) -> float:
    """Min-max normalise to [0, 1]."""
    if hi == lo:
        return 0.5
    return float(np.clip((value - lo) / (hi - lo), 0.0, 1.0))


# ── 1. Fundamental Divergence ─────────────────────────────────────────────────
def compute_fundamental_divergence(
    current: Dict[str, float],
    prior:   Dict[str, float],
    window_label: str = "~21d",
) -> Dict[str, Any]:
    """
    Detects divergence when (growth OR forecast OR inst_flow ↑) AND valuation ↓.
    Confidence: High ≥3 positive factors, Medium=2, Low=1.
    """
    g_up = bool(current.get("growth_proxy",       0) > prior.get("growth_proxy",       0))
    f_up = bool(current.get("forecast_proxy",     0) > prior.get("forecast_proxy",     0))
    i_up = bool(current.get("institutional_flow", 0) > prior.get("institutional_flow", 0))
    v_dn = bool(current.get("valuation_proxy",    0) < prior.get("valuation_proxy",    0))

    factors: List[str] = []
    pos = 0

    factors.append("Revenue/Growth improved (↑)" if g_up else "Revenue/Growth declined (↓)")
    if g_up: pos += 1

    factors.append("Future Forecast improved (↑)" if f_up else "Future Forecast declined (↓)")
    if f_up: pos += 1

    factors.append(
        "Valuation compressed vs prior (↓ = cheaper)"
        if v_dn else "Valuation expanded vs prior (↑ = more expensive)"
    )
    if v_dn: pos += 1

    factors.append("Institutional flow increased (↑)" if i_up else "Institutional flow decreased (↓)")
    if i_up: pos += 1

    detected   = bool((g_up or f_up or i_up) and v_dn)
    confidence = "High" if pos >= 3 else ("Medium" if pos == 2 else "Low")

    return {
        "detected":           detected,
        "confidence":         confidence if detected else "Low",
        "pos_factor_count":   pos,
        "supporting_factors": factors,
        "window":             window_label,
    }


# ── 2. Opportunity Score ──────────────────────────────────────────────────────
OPP_W = {
    "predicted_return_h7": 0.25,
    "valuation_vs_peer":   0.25,
    "institutional_flow":  0.20,
    "fund_divergence":     0.20,
    "peer_position":       0.10,
}


def compute_opportunity_score(
    ticker:             str,
    ticker_snap:        Dict[str, float],
    peer_medians:       Dict[str, float],
    forecast_h7_return: Optional[float],
    fund_divergence:    Dict[str, Any],
    has_dividend:       bool,
) -> Dict[str, Any]:
    evidence: List[str] = []
    pos_fac:  List[str] = []
    neg_fac:  List[str] = []
    comps:    Dict[str, float] = {}

    # Component 1 — Predicted Return H+7
    ret = forecast_h7_return or 0.0
    c1  = _mm(ret, -0.10, 0.10)
    comps["predicted_return_h7"] = c1
    evidence.append(f"Forecast H+7 Return: {ret*100:+.2f}%")
    (pos_fac if ret > 0 else neg_fac).append(
        f"Forecast H+7 {'positive' if ret>0 else 'negative'} ({ret*100:+.2f}%)"
    )

    # Component 2 — Valuation vs Peer (higher val_proxy = cheaper = better)
    tv_v  = ticker_snap.get("valuation_proxy", 0.0)
    pm_v  = peer_medians.get("valuation_proxy", 0.0)
    dv    = tv_v - pm_v
    c2    = _mm(dv, -0.20, 0.20)
    comps["valuation_vs_peer"] = c2
    evidence.append(f"Valuation proxy: {tv_v:.4f} vs peer {pm_v:.4f} (diff {dv:+.4f})")
    (pos_fac if dv > 0 else neg_fac).append(
        "Valuation attractive vs peer" if dv > 0 else "Valuation stretched vs peer"
    )

    # Component 3 — Institutional Flow vs Peer
    tv_i  = ticker_snap.get("institutional_flow", 0.5)
    pm_i  = peer_medians.get("institutional_flow", 0.5)
    di    = tv_i - pm_i
    c3    = _mm(di, -0.5, 0.5)
    comps["institutional_flow"] = c3
    evidence.append(f"Institutional flow: {tv_i:.3f} vs peer {pm_i:.3f} (diff {di:+.3f})")
    (pos_fac if di > 0 else neg_fac).append(
        "Institutional flow above peer" if di > 0 else "Institutional flow below peer"
    )

    # Component 4 — Fundamental Divergence
    fd_ok  = fund_divergence.get("detected", False)
    fd_map = {"High": 1.0, "Medium": 0.6, "Low": 0.2}
    fd_w   = fd_map.get(fund_divergence.get("confidence", "Low"), 0.2)
    c4     = float(fd_w if fd_ok else 1.0 - fd_w)
    comps["fund_divergence"] = c4
    evidence.append(
        f"Fundamental Divergence: {'Detected' if fd_ok else 'Not Detected'}, "
        f"Confidence {fund_divergence.get('confidence','Low')}"
    )
    (pos_fac if fd_ok else neg_fac).append(
        f"Fundamental Divergence {'detected' if fd_ok else 'not detected'} "
        f"({fund_divergence.get('confidence','Low')} conf)"
    )

    # Component 5 — Peer Position (growth + dividend)
    tv_g  = ticker_snap.get("growth_proxy", 0.0)
    pm_g  = peer_medians.get("growth_proxy", 0.0)
    dg    = tv_g - pm_g
    c5    = float(np.clip(_mm(dg, -0.10, 0.10) + (0.1 if has_dividend else 0.0), 0.0, 1.0))
    comps["peer_position"] = c5
    evidence.append(f"Growth: {tv_g:.4f} vs peer {pm_g:.4f} (diff {dg:+.4f})")
    (pos_fac if dg > 0 else neg_fac).append(
        "Growth above peer median" if dg > 0 else "Growth below peer median"
    )
    (pos_fac if has_dividend else neg_fac).append(
        "Recent dividend payment recorded" if has_dividend else "No recent dividend payment"
    )

    raw   = sum(comps[k] * OPP_W[k] for k in OPP_W)
    score = round(float(np.clip(raw * 100, 1.0, 99.0)), 1)
    n_pos = len(pos_fac)
    conf  = "High" if n_pos >= 4 else ("Medium" if n_pos >= 2 else "Low")

    return {
        "score":            score,
        "confidence":       conf,
        "direction":        "Positive" if score >= 50 else "Negative",
        "positive_factors": pos_fac,
        "negative_factors": neg_fac,
        "evidence":         evidence,
        "components":       {k: round(v, 4) for k, v in comps.items()},
    }


# ── 3. Risk Score ─────────────────────────────────────────────────────────────
RISK_W = {
    "neg_return_h7":      0.25,
    "val_stretched":      0.25,
    "inst_outflow":       0.20,
    "fund_deterioration": 0.20,
    "high_volatility":    0.10,
}


def compute_risk_score(
    ticker:             str,
    ticker_snap:        Dict[str, float],
    peer_medians:       Dict[str, float],
    forecast_h7_return: Optional[float],
    fund_divergence:    Dict[str, Any],
) -> Dict[str, Any]:
    evidence: List[str] = []
    neg_fac:  List[str] = []
    comps:    Dict[str, float] = {}

    ret = forecast_h7_return or 0.0
    c1  = _mm(-ret, -0.10, 0.10)
    comps["neg_return_h7"] = c1
    evidence.append(f"Forecast H+7: {ret*100:+.2f}%")
    if ret < 0:
        neg_fac.append(f"Forecast H+7 negative ({ret*100:+.2f}%)")

    tv_v  = ticker_snap.get("valuation_proxy", 0.0)
    pm_v  = peer_medians.get("valuation_proxy", 0.0)
    dv    = pm_v - tv_v   # positive = ticker more expensive than peer
    c2    = _mm(dv, -0.20, 0.20)
    comps["val_stretched"] = c2
    evidence.append(f"Valuation proxy: {tv_v:.4f} vs peer {pm_v:.4f}")
    if dv > 0:
        neg_fac.append("Valuation stretched vs peer")

    tv_i  = ticker_snap.get("institutional_flow", 0.5)
    pm_i  = peer_medians.get("institutional_flow", 0.5)
    di    = pm_i - tv_i   # positive = below peer = outflow risk
    c3    = _mm(di, -0.5, 0.5)
    comps["inst_outflow"] = c3
    evidence.append(f"Institutional flow: {tv_i:.3f} vs peer {pm_i:.3f}")
    if di > 0:
        neg_fac.append("Institutional flow below peer (outflow risk)")

    fd_ok  = fund_divergence.get("detected", False)
    fd_pos = fund_divergence.get("pos_factor_count", 0)
    c4     = float(max(0.0, (4 - fd_pos) / 4.0)) if not fd_ok else 0.2
    comps["fund_deterioration"] = c4
    evidence.append(
        f"Fundamental Divergence: {'Detected' if fd_ok else 'Not Detected'}, "
        f"{fd_pos}/4 factors positive"
    )
    if not fd_ok and fd_pos <= 1:
        neg_fac.append("Fundamental deterioration (multiple factors declining)")

    tv_vol = ticker_snap.get("vol_20d", 0.0)
    pm_vol = peer_medians.get("vol_20d", 0.0)
    dv2    = tv_vol - pm_vol
    c5     = _mm(dv2, -0.01, 0.02)
    comps["high_volatility"] = c5
    evidence.append(f"Vol_20d: {tv_vol:.4f} vs peer {pm_vol:.4f}")
    if dv2 > 0:
        neg_fac.append("Volatility above peer median")

    raw   = sum(comps[k] * RISK_W[k] for k in RISK_W)
    score = round(float(np.clip(raw * 100, 1.0, 99.0)), 1)
    level = "High" if score > 66 else ("Medium" if score > 33 else "Low")

    return {
        "score":            score,
        "level":            level,
        "negative_factors": neg_fac,
        "evidence":         evidence,
        "components":       {k: round(v, 4) for k, v in comps.items()},
    }


# ── 4. Anomaly Flag ───────────────────────────────────────────────────────────
def compute_anomaly_flag(
    clf_acc_h1:     float,
    opp_score:      float,
    risk_score:     float,
    fund_divergence: Dict[str, Any],
) -> bool:
    low_accuracy   = clf_acc_h1 < 0.45
    contradictory  = opp_score > 85 and risk_score > 66
    div_mismatch   = (
        fund_divergence.get("detected", False)
        and fund_divergence.get("confidence") == "High"
        and opp_score < 30
    )
    return bool(low_accuracy or contradictory or div_mismatch)
