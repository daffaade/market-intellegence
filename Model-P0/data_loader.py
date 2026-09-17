"""
data_loader.py — Data Acquisition Layer (Model-P0)
Reuses get_api_data() from unified_data/endpoint_finaldata.py.
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional

# ── Bootstrap sys.path ────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
for _p in [str(_HERE), str(_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from unified_data.endpoint_finaldata import get_api_data

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_TICKERS = ["BBCA", "BBRI", "BMRI", "TLKM", "ANTM", "BUMI"]


def load_price_df(ticker: str, period: str = "10y") -> pd.DataFrame:
    res     = get_api_data(ticker=ticker, data_type="price", period=period)
    records = res.get("data", {}).get("records", [])
    df      = pd.DataFrame(records)

    if df.empty:
        raise ValueError(f"No price data returned for {ticker}")

    df.columns = [c.lower() for c in df.columns]

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df.sort_values("date", inplace=True)
        df.reset_index(drop=True, inplace=True)

    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df.drop_duplicates(subset=["date"], inplace=True)
    df.dropna(subset=["date", "close"], inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def load_fundamental_snapshot(ticker: str) -> Dict[str, Any]:
    snapshot: Dict[str, Any] = {}
    for data_type, period in [
        ("valuation",                 "current"),
        ("forecast",                  "current"),
        ("dividend",                  "10y"),
        ("institutional_transactions","6m"),
        ("peers",                     "current"),
    ]:
        try:
            res = get_api_data(ticker=ticker, data_type=data_type, period=period)
            snapshot[data_type] = res.get("data", {})
        except Exception as exc:
            snapshot[data_type] = {"_error": str(exc)}
    return snapshot


def load_all_tickers(
    tickers: Optional[List[str]] = None,
    price_period: str = "10y",
) -> Dict[str, Dict[str, Any]]:
    tickers = tickers or DEFAULT_TICKERS
    result: Dict[str, Dict[str, Any]] = {}
    for ticker in tickers:
        try:
            price_df     = load_price_df(ticker, price_period)
            fundamentals = load_fundamental_snapshot(ticker)
            result[ticker] = {"price_df": price_df, "fundamentals": fundamentals}
            print(f"  [OK] {ticker} — {len(price_df)} price rows loaded")
        except Exception as exc:
            result[ticker] = {"price_df": pd.DataFrame(), "fundamentals": {}, "_error": str(exc)}
            print(f"  [ERR] {ticker} — {exc}")
    return result
