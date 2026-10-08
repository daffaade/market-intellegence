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

    def analyze(self, symbol: str, anomaly: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Runs forecasting analysis, returning horizon curves, opportunity score, and risk score.
        `anomaly` (the AnomalyModel output) feeds the risk score when available.
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

                # Out-of-sample directional accuracy on the held-out 30%: the forecast
                # only earns weight in the opportunity score when it beats a coin flip.
                h_test = test_df.dropna(subset=[dir_col])
                test_acc = None
                baseline_acc = None
                if len(h_test) >= 20:
                    y_true = h_test[dir_col].values
                    test_pred = clf.predict(scaler.transform(h_test[FEATURE_COLS].values))
                    test_acc = float(accuracy_score(y_true, test_pred))
                    # Accuracy of always guessing the majority direction: in a steady
                    # downtrend "always down" already scores ~70%.
                    up_rate = float(np.mean(y_true))
                    baseline_acc = max(up_rate, 1 - up_rate)

                horizon_curve[f"H+{h}"] = {
                    "predicted_return": round(pred_ret, 5),
                    "direction": pred_dir,
                    "test_accuracy": round(test_acc, 4) if test_acc is not None else None,
                    "baseline_accuracy": round(baseline_acc, 4) if baseline_acc is not None else None,
                    "test_rows": len(h_test),
                }

            last_close = float(df["close"].iloc[-1])
            h7_ret = horizon_curve.get("H+7", {}).get("predicted_return", 0.0)

            h7 = horizon_curve.get("H+7", {})
            acc = h7.get("test_accuracy")
            base = h7.get("baseline_accuracy")
            # Skill = edge over the naive majority-direction guess: 0 with no edge,
            # 1 at +10 points or more. Without an edge the forecast gets no weight.
            skill = float(np.clip((acc - base) / 0.10, 0.0, 1.0)) if acc is not None and base is not None else 0.0

            from ai_engine.models.signal.factor_signal import compute_signals
            signals = compute_signals(
                symbol, df, forecast_h7=h7_ret, forecast_skill=skill, anomaly=anomaly,
            )

            return {
                "status": "success",
                "forecast": {
                    "last_close": last_close,
                    "horizon_curve": horizon_curve,
                    "model_agreement_flag": len(disagreements) == 0,
                    "disagreement_horizons": disagreements,
                    "h7_test_accuracy": acc,
                    "h7_baseline_accuracy": base,
                    "skill": round(skill, 3),
                },
                "fundamental_divergence": signals["fundamental_divergence"],
                "opportunity_signal": signals["opportunity_signal"],
                "risk_signal": signals["risk_signal"],
                "factors": signals["factors"],
                "data_coverage": signals["data_coverage"],
                "fundamentals_source": signals["fundamentals_source"],
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}
