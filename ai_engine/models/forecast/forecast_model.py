"""
forecast_model.py — Self-contained Multi-Horizon Forecast & Signal Engine (ai_engine)
Implements 7 RandomForestClassifier + 7 RandomForestRegressor (H+1 … H+7)
and computes Opportunity Score, Risk Score, and Model Agreement.
"""

from __future__ import annotations
import math
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, mean_absolute_error, mean_squared_error, r2_score

# ── Feature Engineering Utilities ─────────────────────────────────────────────
HORIZONS = list(range(1, 8))   # H+1 … H+7

FEATURE_COLS = [
    "return_1d", "return_5d", "return_20d", "return_60d",
    "vol_20d", "vol_60d", "vol_ratio",
    "price_vs_ma20", "price_vs_ma60", "price_vs_ma200",
    "rsi_14", "intraday_range",
    "growth_proxy", "valuation_proxy", "forecast_proxy", "institutional_flow",
]

# Configurable flag for using smart money
USE_SMART_MONEY = False
if USE_SMART_MONEY:
    FEATURE_COLS.append("smart_money_score")

RF_CLF = dict(n_estimators=100, max_depth=6, random_state=42, n_jobs=-1)
RF_REG = dict(n_estimators=100, max_depth=6, random_state=42, n_jobs=-1)


def _compute_rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(com=window - 1, min_periods=window).mean()
    avg_loss = loss.ewm(com=window - 1, min_periods=window).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def build_features(
    price_df: pd.DataFrame,
    fundamentals: Optional[Dict[str, Any]] = None,
    ticker: str = "TICKER",
) -> pd.DataFrame:
    df = price_df.copy()
    df["ticker"] = ticker

    # Returns
    df["return_1d"] = df["close"].pct_change(1)
    df["return_5d"] = df["close"].pct_change(5)
    df["return_20d"] = df["close"].pct_change(20)
    df["return_60d"] = df["close"].pct_change(60)

    # Volatility
    df["vol_20d"] = df["return_1d"].rolling(20).std()
    df["vol_60d"] = df["return_1d"].rolling(60).std()
    df["vol_ratio"] = df["vol_20d"] / df["vol_60d"].replace(0, np.nan)

    # Moving Average Momentum
    df["ma20"] = df["close"].rolling(20).mean()
    df["ma60"] = df["close"].rolling(60).mean()
    df["ma200"] = df["close"].rolling(200).mean()
    df["price_vs_ma20"] = (df["close"] - df["ma20"]) / df["ma20"].replace(0, np.nan)
    df["price_vs_ma60"] = (df["close"] - df["ma60"]) / df["ma60"].replace(0, np.nan)
    df["price_vs_ma200"] = (df["close"] - df["ma200"]) / df["ma200"].replace(0, np.nan)

    # RSI & Intraday Range
    df["rsi_14"] = _compute_rsi(df["close"], 14)
    if "high" in df.columns and "low" in df.columns:
        df["intraday_range"] = (df["high"] - df["low"]) / df["close"].replace(0, np.nan)
    else:
        df["intraday_range"] = 0.0

    # Fundamental proxies (price-derived defaults)
    df["growth_proxy"] = df["return_20d"]
    df["valuation_proxy"] = -df["return_60d"]
    df["forecast_proxy"] = df["return_20d"] * 1.5

    # Institutional flow proxy via normalized volume z-score -> sigmoid
    if "volume" in df.columns:
        vol_mean = df["volume"].rolling(60).mean()
        vol_std = df["volume"].rolling(60).std()
        raw_flow = (df["volume"] - vol_mean) / vol_std.replace(0, np.nan)
    else:
        raw_flow = pd.Series(0.0, index=df.index)
    df["institutional_flow"] = 1 / (1 + np.exp(-raw_flow.fillna(0)))

    # Optional Smart Money Feature integration
    if USE_SMART_MONEY:
        df["smart_money_score"] = 0.0

    # Labels for H+1 .. H+7
    for h in HORIZONS:
        fut_ret = (df["close"].shift(-h) - df["close"]) / df["close"].replace(0, np.nan)
        df[f"label_ret_{h}"] = fut_ret
        df[f"label_dir_{h}"] = (fut_ret >= 0).astype(int)

    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    return df


def _mm(value: float, lo: float, hi: float) -> float:
    """Min-max normalize to [0, 1]."""
    if hi == lo:
        return 0.5
    return float(np.clip((value - lo) / (hi - lo), 0.0, 1.0))


# ── Signal Engine Helpers ─────────────────────────────────────────────────────
OPP_W = {
    "predicted_return_h7": 0.25,
    "valuation_vs_peer": 0.25,
    "institutional_flow": 0.20,
    "fund_divergence": 0.20,
    "peer_position": 0.10,
}

RISK_W = {
    "neg_return_h7": 0.25,
    "val_stretched": 0.25,
    "inst_outflow": 0.20,
    "fund_deterioration": 0.20,
    "high_volatility": 0.10,
}


def compute_fundamental_divergence(
    current: Dict[str, float],
    prior: Dict[str, float],
    window_label: str = "~21d",
) -> Dict[str, Any]:
    g_up = bool(current.get("growth_proxy", 0) > prior.get("growth_proxy", 0))
    f_up = bool(current.get("forecast_proxy", 0) > prior.get("forecast_proxy", 0))
    i_up = bool(current.get("institutional_flow", 0) > prior.get("institutional_flow", 0))
    v_dn = bool(current.get("valuation_proxy", 0) < prior.get("valuation_proxy", 0))

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

    detected = bool((g_up or f_up or i_up) and v_dn)
    confidence = "High" if pos >= 3 else ("Medium" if pos == 2 else "Low")

    return {
        "detected": detected,
        "confidence": confidence if detected else "Low",
        "pos_factor_count": pos,
        "supporting_factors": factors,
        "window": window_label,
    }


def compute_opportunity_score(
    ticker_snap: Dict[str, float],
    peer_medians: Dict[str, float],
    forecast_h7_return: Optional[float],
    fund_divergence: Dict[str, Any],
    has_dividend: bool = False,
) -> Dict[str, Any]:
    evidence: List[str] = []
    pos_fac: List[str] = []
    neg_fac: List[str] = []
    comps: Dict[str, float] = {}

    ret = forecast_h7_return or 0.0
    c1 = _mm(ret, -0.10, 0.10)
    comps["predicted_return_h7"] = c1
    evidence.append(f"Forecast H+7 Return: {ret*100:+.2f}%")
    (pos_fac if ret > 0 else neg_fac).append(
        f"Forecast H+7 {'positive' if ret>0 else 'negative'} ({ret*100:+.2f}%)"
    )

    tv_v = ticker_snap.get("valuation_proxy", 0.0)
    pm_v = peer_medians.get("valuation_proxy", 0.0)
    dv = tv_v - pm_v
    c2 = _mm(dv, -0.20, 0.20)
    comps["valuation_vs_peer"] = c2
    evidence.append(f"Valuation proxy: {tv_v:.4f} vs peer {pm_v:.4f} (diff {dv:+.4f})")
    (pos_fac if dv > 0 else neg_fac).append(
        "Valuation attractive vs peer" if dv > 0 else "Valuation stretched vs peer"
    )

    tv_i = ticker_snap.get("institutional_flow", 0.5)
    pm_i = peer_medians.get("institutional_flow", 0.5)
    di = tv_i - pm_i
    c3 = _mm(di, -0.5, 0.5)
    comps["institutional_flow"] = c3
    evidence.append(f"Institutional flow: {tv_i:.3f} vs peer {pm_i:.3f} (diff {di:+.3f})")
    (pos_fac if di > 0 else neg_fac).append(
        "Institutional flow above peer" if di > 0 else "Institutional flow below peer"
    )

    fd_ok = fund_divergence.get("detected", False)
    fd_map = {"High": 1.0, "Medium": 0.6, "Low": 0.2}
    fd_w = fd_map.get(fund_divergence.get("confidence", "Low"), 0.2)
    c4 = float(fd_w if fd_ok else 1.0 - fd_w)
    comps["fund_divergence"] = c4
    evidence.append(
        f"Fundamental Divergence: {'Detected' if fd_ok else 'Not Detected'}, "
        f"Confidence {fund_divergence.get('confidence','Low')}"
    )
    (pos_fac if fd_ok else neg_fac).append(
        f"Fundamental Divergence {'detected' if fd_ok else 'not detected'} "
        f"({fund_divergence.get('confidence','Low')} conf)"
    )

    tv_g = ticker_snap.get("growth_proxy", 0.0)
    pm_g = peer_medians.get("growth_proxy", 0.0)
    dg = tv_g - pm_g
    c5 = float(np.clip(_mm(dg, -0.10, 0.10) + (0.1 if has_dividend else 0.0), 0.0, 1.0))
    comps["peer_position"] = c5
    evidence.append(f"Growth: {tv_g:.4f} vs peer {pm_g:.4f} (diff {dg:+.4f})")
    (pos_fac if dg > 0 else neg_fac).append(
        "Growth above peer median" if dg > 0 else "Growth below peer median"
    )

    raw = sum(comps[k] * OPP_W[k] for k in OPP_W)
    score = round(float(np.clip(raw * 100, 1.0, 99.0)), 1)
    n_pos = len(pos_fac)
    conf = "High" if n_pos >= 4 else ("Medium" if n_pos >= 2 else "Low")

    return {
        "score": score,
        "confidence": conf,
        "direction": "Positive" if score >= 50 else "Negative",
        "positive_factors": pos_fac,
        "negative_factors": neg_fac,
        "evidence": evidence,
        "components": {k: round(v, 4) for k, v in comps.items()},
    }


def compute_risk_score(
    ticker_snap: Dict[str, float],
    peer_medians: Dict[str, float],
    forecast_h7_return: Optional[float],
    fund_divergence: Dict[str, Any],
) -> Dict[str, Any]:
    evidence: List[str] = []
    neg_fac: List[str] = []
    comps: Dict[str, float] = {}

    ret = forecast_h7_return or 0.0
    c1 = _mm(-ret, -0.10, 0.10)
    comps["neg_return_h7"] = c1
    evidence.append(f"Forecast H+7: {ret*100:+.2f}%")
    if ret < 0:
        neg_fac.append(f"Forecast H+7 negative ({ret*100:+.2f}%)")

    tv_v = ticker_snap.get("valuation_proxy", 0.0)
    pm_v = peer_medians.get("valuation_proxy", 0.0)
    dv = pm_v - tv_v
    c2 = _mm(dv, -0.20, 0.20)
    comps["val_stretched"] = c2
    evidence.append(f"Valuation proxy: {tv_v:.4f} vs peer {pm_v:.4f}")
    if dv > 0:
        neg_fac.append("Valuation stretched vs peer")

    tv_i = ticker_snap.get("institutional_flow", 0.5)
    pm_i = peer_medians.get("institutional_flow", 0.5)
    di = pm_i - tv_i
    c3 = _mm(di, -0.5, 0.5)
    comps["inst_outflow"] = c3
    evidence.append(f"Institutional flow: {tv_i:.3f} vs peer {pm_i:.3f}")
    if di > 0:
        neg_fac.append("Institutional flow below peer (outflow risk)")

    fd_ok = fund_divergence.get("detected", False)
    fd_pos = fund_divergence.get("pos_factor_count", 0)
    c4 = float(max(0.0, (4 - fd_pos) / 4.0)) if not fd_ok else 0.2
    comps["fund_deterioration"] = c4
    evidence.append(
        f"Fundamental Divergence: {'Detected' if fd_ok else 'Not Detected'}, "
        f"{fd_pos}/4 factors positive"
    )
    if not fd_ok and fd_pos <= 1:
        neg_fac.append("Fundamental deterioration (multiple factors declining)")

    tv_vol = ticker_snap.get("vol_20d", 0.0)
    pm_vol = peer_medians.get("vol_20d", 0.0)
    dv2 = tv_vol - pm_vol
    c5 = _mm(dv2, -0.01, 0.02)
    comps["high_volatility"] = c5
    evidence.append(f"Vol_20d: {tv_vol:.4f} vs peer {pm_vol:.4f}")
    if dv2 > 0:
        neg_fac.append("Volatility above peer median")

    raw = sum(comps[k] * RISK_W[k] for k in RISK_W)
    score = round(float(np.clip(raw * 100, 1.0, 99.0)), 1)
    level = "High" if score > 66 else ("Medium" if score > 33 else "Low")

    return {
        "score": score,
        "level": level,
        "negative_factors": neg_fac,
        "evidence": evidence,
        "components": {k: round(v, 4) for k, v in comps.items()},
    }


# ── ForecastModel Class ───────────────────────────────────────────────────────
class ForecastModel:
    def __init__(self, data_loader=None):
        self.data_loader = data_loader

    def _fetch_price_df(self, symbol: str) -> pd.DataFrame:
        """Fetches historical price df via DataLoader or fallback."""
        if self.data_loader:
            price_res = self.data_loader.get_price(symbol, period="10y")
            val = price_res.get("value") if isinstance(price_res, dict) else None
            if isinstance(val, dict) and "records" in val:
                df = pd.DataFrame(val["records"])
                if not df.empty:
                    df.columns = [c.lower() for c in df.columns]
                    if "date" in df.columns:
                        df["date"] = pd.to_datetime(df["date"], errors="coerce")
                        df.sort_values("date", inplace=True)
                        df.reset_index(drop=True, inplace=True)
                    for col in ["open", "high", "low", "close", "volume"]:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors="coerce")
                    df.dropna(subset=["close"], inplace=True)
                    return df

        # Fallback to yfinance if not available from data_loader
        try:
            import yfinance as yf
            ticker_yf = f"{symbol}.JK" if not symbol.endswith(".JK") else symbol
            raw = yf.download(ticker_yf, period="5y", progress=False)
            if not raw.empty:
                if isinstance(raw.columns, pd.MultiIndex):
                    raw.columns = [c[0].lower() for c in raw.columns]
                else:
                    raw.columns = [c.lower() for c in raw.columns]
                raw.reset_index(inplace=True)
                raw.rename(columns={"index": "date", "Date": "date"}, inplace=True)
                return raw
        except Exception:
            pass

        return pd.DataFrame()

    def analyze(self, symbol: str) -> Dict[str, Any]:
        """
        Runs forecasting analysis, returning horizon curves, opportunity score, and risk score.
        """
        try:
            df = self._fetch_price_df(symbol)
            if df.empty or len(df) < 60:
                return {
                    "status": "error",
                    "message": f"Insufficient price history for {symbol}"
                }

            features_df = build_features(df, ticker=symbol)
            clean_df = features_df.dropna(subset=FEATURE_COLS).copy()

            if len(clean_df) < 30:
                return {
                    "status": "error",
                    "message": "Insufficient feature rows after engineering"
                }

            # Train models for each horizon
            # Use 70% train / 30% test split
            split_idx = int(len(clean_df) * 0.7)
            train_df = clean_df.iloc[:split_idx]
            test_df = clean_df.iloc[split_idx:]

            horizon_curve = {}
            disagreements = []

            latest_row = clean_df[FEATURE_COLS].iloc[-1:].values

            for h in HORIZONS:
                dir_col = f"label_dir_{h}"
                ret_col = f"label_ret_{h}"
                
                h_train = train_df.dropna(subset=[dir_col, ret_col])
                if len(h_train) < 20:
                    continue

                X_tr = h_train[FEATURE_COLS].values
                y_dir = h_train[dir_col].values
                y_ret = h_train[ret_col].values

                scaler = StandardScaler()
                X_tr_sc = scaler.fit_transform(X_tr)

                clf = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42, n_jobs=-1)
                clf.fit(X_tr_sc, y_dir)

                reg = RandomForestRegressor(n_estimators=50, max_depth=5, random_state=42, n_jobs=-1)
                reg.fit(X_tr_sc, y_ret)

                # Inference on latest row
                latest_sc = scaler.transform(latest_row)
                pred_dir = int(clf.predict(latest_sc)[0])
                pred_ret = float(reg.predict(latest_sc)[0])

                reg_dir = 1 if pred_ret >= 0 else 0
                if pred_dir != reg_dir:
                    disagreements.append(h)

                horizon_curve[f"H+{h}"] = {
                    "predicted_return": round(pred_ret, 5),
                    "direction": pred_dir
                }

            last_close = float(df["close"].iloc[-1])
            h7_ret = horizon_curve.get("H+7", {}).get("predicted_return", 0.0)

            # Snapshots for Signal Engine
            curr_snap = clean_df.iloc[-1].to_dict()
            prior_snap = clean_df.iloc[-21].to_dict() if len(clean_df) >= 22 else curr_snap
            peer_medians = {
                "growth_proxy": 0.01,
                "valuation_proxy": 0.0,
                "institutional_flow": 0.5,
                "vol_20d": 0.02
            }

            fund_div = compute_fundamental_divergence(curr_snap, prior_snap)
            opp_sig = compute_opportunity_score(curr_snap, peer_medians, h7_ret, fund_div)
            risk_sig = compute_risk_score(curr_snap, peer_medians, h7_ret, fund_div)

            return {
                "status": "success",
                "forecast": {
                    "last_close": last_close,
                    "horizon_curve": horizon_curve,
                    "model_agreement_flag": len(disagreements) == 0,
                    "disagreement_horizons": disagreements
                },
                "fundamental_divergence": fund_div,
                "opportunity_signal": opp_sig,
                "risk_signal": risk_sig
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}
