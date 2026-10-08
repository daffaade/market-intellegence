"""
Macro sensitivity: how a stock's weekly return has moved with the market and
with macro variables over the last two years (correlational, not causal).

For each variable a univariate regression of the stock's weekly return on the
variable's weekly change gives a beta ("when X moves 1%, the stock moved b% on
average"), the correlation, and a t-test on the beta. The latest one-month move
of each variable times its beta shows how much of the stock's recent move the
relationship would account for.

This replaces an earlier implementation that crashed (class-level call to an
instance method) and counted a daily change in a price proxy as a "forecast
revision", which fired on most days and made its co-occurrence rate meaningless.
"""
from __future__ import annotations

import math
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from scipy import stats

FACTORS = [
    # key, yfinance ticker, label, how to read a positive move
    ("ihsg", "^JKSE", "IHSG", "IHSG naik"),
    ("usdidr", "IDR=X", "USD/IDR", "rupiah melemah"),
    ("brent", "BZ=F", "Minyak Brent", "harga minyak naik"),
    ("gold", "GC=F", "Emas", "harga emas naik"),
]
SIGNIFICANCE = 0.05
MIN_WEEKS = 52

_cache: Dict[str, Any] = {}
_lock = threading.Lock()


def _weekly_closes(tickers: List[str]) -> pd.DataFrame:
    import yfinance as yf
    raw = yf.download(" ".join(tickers), period="2y", progress=False, auto_adjust=True, group_by="column")
    close = raw["Close"]
    if isinstance(close, pd.Series):
        close = close.to_frame(tickers[0])
    close.index = pd.to_datetime(close.index).tz_localize(None)
    return close.resample("W-FRI").last()


def _factor_closes() -> pd.DataFrame:
    with _lock:
        hit = _cache.get("factors")
        if hit and time.time() - hit[0] < 6 * 3600:
            return hit[1]
    closes = _weekly_closes([f[1] for f in FACTORS])
    with _lock:
        _cache["factors"] = (time.time(), closes)
    return closes


def _id(text: str) -> str:
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


def run_macro_impact(ticker: str) -> Dict[str, Any]:
    sym = ticker.upper().replace(".JK", "").strip()
    base = {"ticker": sym, "as_of": datetime.now().strftime("%Y-%m-%d"), "sensitivities": [],
            "method": "Regresi return mingguan 2 tahun (korelasional, bukan kausal)"}
    try:
        stock = _weekly_closes([f"{sym}.JK"]).iloc[:, 0]
        factors = _factor_closes()
    except Exception as e:
        return {**base, "data_quality": "missing", "error": str(e)}

    s_ret = stock.pct_change()
    out = []
    for key, yf_ticker, label, reading in FACTORS:
        if yf_ticker not in factors:
            continue
        f_ret = factors[yf_ticker].pct_change()
        both = pd.concat([s_ret, f_ret], axis=1, keys=["s", "f"]).dropna()
        if len(both) < MIN_WEEKS:
            continue
        res = stats.linregress(both["f"], both["s"])
        beta, r, p = float(res.slope), float(res.rvalue), float(res.pvalue)
        significant = p < SIGNIFICANCE

        # Last ~1 month (4 weeks) move of the variable and what the beta implies.
        recent = factors[yf_ticker].dropna()
        move_1m = float(recent.iloc[-1] / recent.iloc[-5] - 1) if len(recent) > 5 else None
        implied = beta * move_1m if move_1m is not None and significant else None

        direction = "searah" if beta > 0 else "berlawanan arah"
        out.append({
            "key": key,
            "label": label,
            "beta": round(beta, 3),
            "correlation": round(r, 3),
            "p_value": round(p, 4),
            "significant": significant,
            "n_weeks": int(len(both)),
            "move_1m_pct": round(move_1m * 100, 2) if move_1m is not None else None,
            "implied_move_1m_pct": round(implied * 100, 2) if implied is not None else None,
            "interpretation": (
                f"Saat {reading} 1%, {sym} rata-rata bergerak {_id(f'{beta:+.2f}')}% ({direction}); "
                f"korelasi {_id(f'{r:.2f}')}"
                + ("" if significant else ", tidak signifikan secara statistik")
            ),
        })

    out.sort(key=lambda x: (not x["significant"], -abs(x["correlation"])))
    strongest = next((x for x in out if x["significant"] and x["key"] != "ihsg"), None)
    return {
        **base,
        "sensitivities": out,
        "dominant_macro": strongest["label"] if strongest else None,
        "data_quality": "ok" if out else "missing",
        "data_source": "yfinance",
    }
