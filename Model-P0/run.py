"""
run.py — Main Orchestrator, Model-P0 Intelligence Engine
=========================================================
Fully self-contained entry point. Run from ANYWHERE:

    python Model-P0/run.py
    python Model-P0/run.py BBCA BBRI BMRI TLKM ANTM

All sibling modules (data_loader, feature_engineering, etc.) are loaded
by inserting the folder of this file into sys.path at startup.
"""

import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# ── Bootstrap: add Model-P0 dir & project root to sys.path ──────────────────
_HERE     = Path(__file__).resolve().parent       # …/Model-P0
_ROOT     = _HERE.parent                          # …/projek
for _p in [str(_HERE), str(_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ── Internal imports (sibling modules, no relative dots) ─────────────────────
import data_loader        as _dl
import feature_engineering as _fe
import forecast_model      as _fm
import peer_analysis       as _pa
import signal_engine       as _se

PRIOR_WINDOW = 21   # trading days for divergence comparison


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline
# ─────────────────────────────────────────────────────────────────────────────

def run_pipeline(
    tickers: Optional[List[str]] = None,
) -> Tuple[List[Dict[str, Any]], Dict[int, Dict[str, Any]]]:
    """
    Full P0 pipeline. Returns (results_list, forecast_results_dict).
    """
    tickers = tickers or _dl.DEFAULT_TICKERS
    ts_now  = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    FCOLS   = _fe.FEATURE_COLS

    # ── 1. Load data ─────────────────────────────────────────────────────────
    print("\n[1/7] Loading data …")
    raw_data = _dl.load_all_tickers(tickers)

    # ── 2. Feature engineering ───────────────────────────────────────────────
    print("\n[2/7] Feature engineering …")
    feature_dfs: Dict[str, pd.DataFrame] = {}
    for ticker, payload in raw_data.items():
        price_df     = payload.get("price_df", pd.DataFrame())
        fundamentals = payload.get("fundamentals", {})
        if price_df.empty:
            print(f"  [SKIP] {ticker} — no price data")
            continue
        try:
            df = _fe.build_features(price_df, fundamentals, ticker)
            df = _fe.add_horizon_labels(df)
            df.dropna(subset=FCOLS[:4], inplace=True)
            feature_dfs[ticker] = df
            print(f"  [OK] {ticker} — {len(df)} rows after feature engineering")
        except Exception as exc:
            print(f"  [ERR] {ticker} feature engineering — {exc}")

    if not feature_dfs:
        print("No valid feature data — aborting.")
        return [], {}

    # ── 3. Train multi-horizon models (all tickers combined) ─────────────────
    print("\n[3/7] Training multi-horizon models (all tickers combined) …")
    df_combined      = pd.concat(list(feature_dfs.values()), ignore_index=True)
    forecast_results = _fm.train_all_horizons(df_combined)

    # ── 4. Peer snapshots & medians ──────────────────────────────────────────
    print("\n[4/7] Computing peer medians …")
    ticker_snapshots: Dict[str, Dict[str, float]] = {
        t: _pa.build_ticker_snapshot(df)
        for t, df in feature_dfs.items()
    }
    peer_medians = _pa.compute_peer_medians(ticker_snapshots)
    print(f"  Peer medians computed for {len(peer_medians)} metrics")

    # ── 5-10. Per-ticker signals ──────────────────────────────────────────────
    print("\n[5/7] Generating signals per ticker …")
    results: List[Dict[str, Any]] = []

    for ticker in tickers:
        if ticker not in feature_dfs:
            results.append({
                "ticker":    ticker,
                "error":     "No feature data available",
                "timestamp": ts_now,
            })
            continue

        df           = feature_dfs[ticker]
        fundamentals = raw_data[ticker].get("fundamentals", {})
        snap         = ticker_snapshots[ticker]

        # ── Prior snapshot (~21 trading days ago) for divergence ──────────────
        fd_keys    = ["growth_proxy", "forecast_proxy", "institutional_flow", "valuation_proxy"]
        prior_row  = df.iloc[-PRIOR_WINDOW - 1] if len(df) > PRIOR_WINDOW else df.iloc[0]
        prior_snap = {}
        for k in fd_keys:
            try:
                v = float(prior_row[k])
                prior_snap[k] = v if not np.isnan(v) else 0.0
            except Exception:
                prior_snap[k] = 0.0
        curr_snap = {k: snap.get(k, 0.0) for k in fd_keys}

        # ── Forecast curve H+1..H+7 ───────────────────────────────────────────
        latest_vec   = np.array([snap.get(c, 0.0) for c in FCOLS]).reshape(1, -1)
        forecast_out = _fm.generate_forecast_curve(forecast_results, latest_vec)

        h7_entry  = forecast_out["horizon_curve"].get("H+7", {})
        h7_return: Optional[float] = h7_entry.get("predicted_return")

        # ── Fundamental Divergence ────────────────────────────────────────────
        fund_div = _se.compute_fundamental_divergence(
            curr_snap, prior_snap, f"~{PRIOR_WINDOW}d"
        )

        # ── Peer relative position ────────────────────────────────────────────
        peer_pos = _pa.peer_relative_position(snap, peer_medians)

        # ── Opportunity Signal ────────────────────────────────────────────────
        div_flag = _pa.has_recent_dividend(fundamentals)
        opp      = _se.compute_opportunity_score(
            ticker, snap, peer_medians, h7_return, fund_div, div_flag
        )

        # ── Risk Signal ───────────────────────────────────────────────────────
        risk = _se.compute_risk_score(
            ticker, snap, peer_medians, h7_return, fund_div
        )

        # ── Anomaly flag ──────────────────────────────────────────────────────
        clf_acc_h1 = forecast_results.get(1, {}).get("clf_acc", 0.5)
        anomaly    = _se.compute_anomaly_flag(
            clf_acc_h1, opp["score"], risk["score"], fund_div
        )

        last_close = float(df["close"].iloc[-1]) if not df.empty else None

        results.append({
            "ticker": ticker,
            "forecast": {
                "last_close":            last_close,
                "horizon_curve":         forecast_out["horizon_curve"],
                "model_agreement_flag":  forecast_out["model_agreement_flag"],
                "disagreement_horizons": forecast_out["disagreement_horizons"],
            },
            "fundamental_divergence": fund_div,
            "peer_analysis": {
                k: {
                    "ticker_val":  v["ticker_val"],
                    "peer_median": v["peer_median"],
                    "diff":        v["diff"],
                    "position":    v["position"],
                }
                for k, v in peer_pos.items()
            },
            "opportunity_signal": {
                "score":            opp["score"],
                "confidence":       opp["confidence"],
                "direction":        opp["direction"],
                "positive_factors": opp["positive_factors"],
                "negative_factors": opp["negative_factors"],
                "evidence":         opp["evidence"],
            },
            "risk_signal": {
                "score":            risk["score"],
                "level":            risk["level"],
                "negative_factors": risk["negative_factors"],
                "evidence":         risk["evidence"],
            },
            "anomaly":   bool(anomaly),
            "period":    "10y",
            "timestamp": ts_now,
        })

        print(
            f"  [OK] {ticker}  "
            f"opp={opp['score']}  risk={risk['score']}  "
            f"anomaly={anomaly}"
        )

    return results, forecast_results


# ─────────────────────────────────────────────────────────────────────────────
# JSON serialiser
# ─────────────────────────────────────────────────────────────────────────────

def _safe(obj):
    if isinstance(obj, np.integer):  return int(obj)
    if isinstance(obj, np.floating): return float(obj)
    if isinstance(obj, np.bool_):    return bool(obj)
    if isinstance(obj, np.ndarray):  return obj.tolist()
    raise TypeError(f"{type(obj).__name__} is not JSON serializable")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tickers = sys.argv[1:] if len(sys.argv) > 1 else None

    results, forecast_results = run_pipeline(tickers)

    # ── JSON output ───────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("MODEL-P0  OUTPUT")
    print("=" * 70)
    print(json.dumps(results, indent=2, ensure_ascii=False, default=_safe))

    # ── Accuracy table ────────────────────────────────────────────────────────
    if forecast_results:
        print("\n" + "=" * 70)
        print("ACCURACY TABLE  (per horizon, H+1 → H+7)")
        print("=" * 70)
        print(_fm.build_accuracy_table(forecast_results))
