"""
feature_engineering.py — Cleaning & Feature Engineering (Model-P0)
Implements §3 & §4 of implementation-plan-forecast-signal-module.md
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
for _p in [str(_HERE), str(_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── RSI ───────────────────────────────────────────────────────────────────────
def _compute_rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta    = series.diff()
    gain     = delta.clip(lower=0)
    loss     = (-delta).clip(lower=0)
    avg_gain = gain.ewm(com=window - 1, min_periods=window).mean()
    avg_loss = loss.ewm(com=window - 1, min_periods=window).mean()
    rs  = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


HORIZONS = list(range(1, 8))   # H+1 … H+7

FEATURE_COLS = [
    "return_1d", "return_5d", "return_20d", "return_60d",
    "vol_20d", "vol_60d", "vol_ratio",
    "price_vs_ma20", "price_vs_ma60", "price_vs_ma200",
    "rsi_14", "intraday_range",
    "growth_proxy", "valuation_proxy", "forecast_proxy", "institutional_flow",
]


def build_features(
    price_df: pd.DataFrame,
    fundamentals: Dict[str, Any],
    ticker: str,
) -> pd.DataFrame:
    df = price_df.copy()
    df["ticker"] = ticker

    # Returns
    df["return_1d"]  = df["close"].pct_change(1)
    df["return_5d"]  = df["close"].pct_change(5)
    df["return_20d"] = df["close"].pct_change(20)
    df["return_60d"] = df["close"].pct_change(60)

    # Volatility
    df["vol_20d"]  = df["return_1d"].rolling(20).std()
    df["vol_60d"]  = df["return_1d"].rolling(60).std()
    df["vol_ratio"] = df["vol_20d"] / df["vol_60d"].replace(0, np.nan)

    # MA momentum
    df["ma20"]  = df["close"].rolling(20).mean()
    df["ma60"]  = df["close"].rolling(60).mean()
    df["ma200"] = df["close"].rolling(200).mean()
    df["price_vs_ma20"]  = (df["close"] - df["ma20"])  / df["ma20"].replace(0, np.nan)
    df["price_vs_ma60"]  = (df["close"] - df["ma60"])  / df["ma60"].replace(0, np.nan)
    df["price_vs_ma200"] = (df["close"] - df["ma200"]) / df["ma200"].replace(0, np.nan)

    # RSI & intraday range
    df["rsi_14"] = _compute_rsi(df["close"], 14)
    if "high" in df.columns and "low" in df.columns:
        df["intraday_range"] = (df["high"] - df["low"]) / df["close"].replace(0, np.nan)
    else:
        df["intraday_range"] = 0.0

    # Fundamental proxies (price-derived defaults)
    df["growth_proxy"]    = df["return_20d"]
    df["valuation_proxy"] = -df["return_60d"]
    df["forecast_proxy"]  = df["return_20d"] * 1.5

    # Institutional flow proxy via normalised volume z-score → sigmoid
    if "volume" in df.columns:
        vol_mean = df["volume"].rolling(60).mean()
        vol_std  = df["volume"].rolling(60).std()
        raw_flow = (df["volume"] - vol_mean) / vol_std.replace(0, np.nan)
    else:
        raw_flow = pd.Series(0.0, index=df.index)
    df["institutional_flow"] = 1 / (1 + np.exp(-raw_flow.fillna(0)))

    df = _enrich_from_fundamentals(df, fundamentals)
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    return df


def _enrich_from_fundamentals(df: pd.DataFrame, fundamentals: Dict[str, Any]) -> pd.DataFrame:
    # Valuation: forward P/E
    val    = fundamentals.get("valuation", {})
    fwd_pe = val.get("forward_pe") if isinstance(val, dict) else None
    if fwd_pe is not None:
        try:
            df["valuation_proxy"] = float(fwd_pe) / 30.0
        except (TypeError, ValueError):
            pass

    # Forecast: EPS estimate
    fcast = fundamentals.get("forecast", {})
    if isinstance(fcast, dict) and fcast.get("records"):
        try:
            recs    = fcast["records"]
            rec     = recs[-1] if isinstance(recs, list) else fcast
            eps_est = rec.get("eps_estimate")
            if eps_est is not None:
                df["forecast_proxy"] = float(eps_est) / 1000.0
        except (TypeError, ValueError, IndexError):
            pass

    # Institutional: net buy/sell flow
    inst = fundamentals.get("institutional_transactions", {})
    if isinstance(inst, dict) and inst.get("records"):
        try:
            recs     = inst["records"]
            net_vals = []
            if isinstance(recs, list):
                for r in recs[-20:]:
                    b = r.get("buy_value",  0) or 0
                    s = r.get("sell_value", 0) or 0
                    net_vals.append(b - s)
            if net_vals:
                mean_net = float(np.mean(net_vals))
                df["institutional_flow"] = float(1 / (1 + np.exp(-mean_net / 1e11)))
        except Exception:
            pass

    return df


def add_horizon_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Adds label_dir_h and label_ret_h for h = 1..7."""
    for h in HORIZONS:
        future_close         = df["close"].shift(-h)
        df[f"label_dir_{h}"] = (future_close > df["close"]).astype(float)
        df[f"label_ret_{h}"] = (future_close - df["close"]) / df["close"].replace(0, np.nan)
    return df


def temporal_split(df: pd.DataFrame, train_ratio: float = 0.6) -> Tuple[pd.DataFrame, pd.DataFrame]:
    split_idx = int(len(df) * train_ratio)
    return df.iloc[:split_idx].copy(), df.iloc[split_idx:].copy()
