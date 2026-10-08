"""
Catalyst Detector - ai_engine/models/catalyst/catalyst_detector.py
"""
import sys
import yaml
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

CURRENT_DIR = Path(__file__).resolve().parent
AI_ENGINE_DIR = CURRENT_DIR.parent.parent
ROOT_DIR = AI_ENGINE_DIR.parent
for _p in [str(CURRENT_DIR), str(AI_ENGINE_DIR), str(ROOT_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

CONFIG_PATH = AI_ENGINE_DIR / "config" / "catalyst.yaml"
LOOKBACK = 20  # sessions scanned for catalysts


def _id(text: str) -> str:
    """'1,234.5' -> '1.234,5' (Indonesian separators)."""
    return text.replace(",", "_").replace(".", ",").replace("_", ".")

class CatalystDetector:
    def __init__(self, data_loader=None):
        self.data_loader = data_loader
        self._load_config()

    def _load_config(self):
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r") as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {
                "market_layer": {
                    "volume_spike": {"window": 60, "z_score_threshold": 3.0},
                    "gap_up_down": {"atr_window": 14, "atr_multiplier": 1.5},
                    "abnormal_return": {"window": 20, "residual_threshold": 0.05},
                    "breakout": {"window": 252}
                }
            }

    @staticmethod
    def _normalize(df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return pd.DataFrame()
        df = df.copy()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]
        df.columns = [str(c).capitalize() for c in df.columns]
        df.index = pd.to_datetime(df.index).tz_localize(None)
        return df.dropna(subset=["Close"])

    def _get_ohlcv(self, symbol: str, as_of: Optional[str] = None) -> pd.DataFrame:
        # Two years so the 52-week breakout check has a full prior window.
        df = None
        if self.data_loader and hasattr(self.data_loader, "get_historical_data"):
            df = self.data_loader.get_historical_data(symbol, period="2y")
        if df is None or df.empty:
            import yfinance as yf
            df = yf.download(f"{symbol}.JK", period="2y", progress=False, auto_adjust=False)
        df = self._normalize(df)
        return df.loc[:as_of] if as_of and not df.empty else df

    def _get_benchmark(self, as_of: Optional[str] = None) -> pd.Series:
        try:
            from ai_engine.models.signal.factor_signal import ihsg_close
            s = ihsg_close()
        except Exception:
            s = None
        if s is None or s.empty:
            return pd.Series(dtype=float)
        return s.loc[:as_of] if as_of else s

    def analyze(self, symbol: str, as_of: Optional[str] = None) -> Dict[str, Any]:
        """
        Scans the last LOOKBACK sessions (not just the latest day) for market
        catalysts: volume spikes, gaps, abnormal returns vs IHSG, 52-week breakouts,
        corporate actions and unusually large foreign flow. Recent events weigh more.
        """
        symbol = symbol.upper().replace(".JK", "")
        default_response = {
            "ticker": symbol,
            "as_of": as_of or datetime.today().strftime('%Y-%m-%d'),
            "catalyst_score": 0.0,
            "net_direction": "None",
            "events": [],
            "data_quality_flags": []
        }
        try:
            df = self._get_ohlcv(symbol, as_of)
            if df.empty:
                default_response["data_quality_flags"].append("empty_price_data")
                return default_response
            if len(df) < 80:
                default_response["data_quality_flags"].append("insufficient_price_data")
                return default_response
            cfg = self.config["market_layer"]
            events: List[Dict[str, Any]] = []
            close, ret = df["Close"], df["Close"].pct_change()
            recent = df.index[-LOOKBACK:]

            def add(date, kind, direction, strength, evidence, confidence="high"):
                events.append({
                    "date": str(pd.Timestamp(date).date()), "type": kind, "layer": "market",
                    "direction": direction, "strength": round(float(min(1.0, strength)), 3),
                    "confidence": confidence, "evidence": [evidence],
                })

            # 1. Volume spike
            w = cfg["volume_spike"]["window"]
            vol = df["Volume"].astype(float)
            z = (vol - vol.rolling(w).mean().shift(1)) / vol.rolling(w).std().shift(1)
            for d in recent:
                if z.get(d, 0) > cfg["volume_spike"]["z_score_threshold"]:
                    r = ret.get(d, 0) or 0
                    add(d, "volume_spike", "Positive" if r > 0 else "Negative", z[d] / 6,
                        f"Volume {_id(f'{vol[d] / vol.rolling(w).mean().shift(1)[d]:,.1f}')}x rata-rata {w} hari, harga {_id(f'{r*100:+.1f}')}%")

            # 2. Gap up/down vs ATR
            if {"Open", "High", "Low"} <= set(df.columns):
                aw, mult = cfg["gap_up_down"]["atr_window"], cfg["gap_up_down"]["atr_multiplier"]
                prev_close = close.shift(1)
                tr = pd.concat([df["High"] - df["Low"], (df["High"] - prev_close).abs(), (df["Low"] - prev_close).abs()], axis=1).max(axis=1)
                atr = tr.rolling(aw).mean().shift(1)
                gap = df["Open"] - prev_close
                for d in recent:
                    if atr.get(d) and abs(gap[d]) > mult * atr[d]:
                        add(d, "gap_up" if gap[d] > 0 else "gap_down", "Positive" if gap[d] > 0 else "Negative",
                            abs(gap[d]) / atr[d] / 4, f"Harga dibuka {_id(f'{gap[d] / prev_close[d] * 100:+.1f}')}% dari penutupan sebelumnya ({_id(f'{abs(gap[d]) / atr[d]:.1f}')}x ATR)")

            # 3. Abnormal return vs IHSG (market model on the prior 120 sessions)
            bench = self._get_benchmark(as_of)
            if not bench.empty:
                b = bench.pct_change().reindex(df.index)
                both = pd.concat([ret, b], axis=1, keys=["s", "m"]).dropna()
                est = both.iloc[-(120 + LOOKBACK):-LOOKBACK] if len(both) > 120 + LOOKBACK else pd.DataFrame()
                if len(est) >= 60:
                    beta = est["s"].cov(est["m"]) / est["m"].var()
                    alpha = est["s"].mean() - beta * est["m"].mean()
                    resid_sd = (est["s"] - alpha - beta * est["m"]).std()
                    thr = max(cfg["abnormal_return"]["residual_threshold"], 3 * resid_sd)
                    for d in recent:
                        if d in both.index:
                            ar = both.at[d, "s"] - alpha - beta * both.at[d, "m"]
                            if abs(ar) > thr:
                                add(d, "abnormal_return", "Positive" if ar > 0 else "Negative", abs(ar) / (2 * thr),
                                    f"Return abnormal {_id(f'{ar*100:+.1f}')}% di luar pergerakan IHSG")

            # 4. 52-week breakout (first close beyond the prior 252-session range)
            bw = cfg["breakout"]["window"]
            if len(df) > bw + LOOKBACK:
                hi = df["High"].rolling(bw).max().shift(1) if "High" in df else close.rolling(bw).max().shift(1)
                lo = df["Low"].rolling(bw).min().shift(1) if "Low" in df else close.rolling(bw).min().shift(1)
                up = [d for d in recent if close[d] > hi[d]]
                dn = [d for d in recent if close[d] < lo[d]]
                if up:
                    add(up[0], "breakout_high", "Positive", 0.8, "Harga menembus level tertinggi 52 minggu")
                if dn:
                    add(dn[0], "breakout_low", "Negative", 0.8, "Harga menembus level terendah 52 minggu")

            # 5. Corporate actions (ex-dates) in the window
            try:
                import yfinance as yf
                actions = yf.Ticker(f"{symbol}.JK").actions
                if actions is not None and not actions.empty:
                    actions.index = pd.to_datetime(actions.index).tz_localize(None)
                    for d, row in actions[actions.index >= recent[0]].iterrows():
                        dps = float(row.get("Dividends") or 0)
                        if dps > 0:
                            add(d, "dividend_ex", "Neutral", 0.3, f"Tanggal ex dividen Rp {_id(f'{dps:,.1f}')} per saham", "medium")
                        if (row.get("Stock Splits") or 0) > 0:
                            add(d, "stock_split", "Neutral", 0.3, f"Stock split {row['Stock Splits']:g}:1", "medium")
            except Exception:
                default_response["data_quality_flags"].append("corporate_actions_unavailable")

            # 6. Unusually large foreign flow (Sectors, cached; no new fetch here)
            try:
                from data_processing.data_sectors.market_series import get_foreign_flow
                ff = get_foreign_flow(symbol)
                pts = [p for p in (ff or {}).get("points", []) if p.get("net") is not None]
                if len(pts) >= 30:
                    # Reference = mean absolute daily net over the sessions before the
                    # window (a median can sit near zero and inflate the ratio).
                    ref = float(np.mean([abs(float(p["net"])) for p in pts[:-LOOKBACK]]))
                    surges = [p for p in pts[-LOOKBACK:] if ref > 0 and abs(float(p["net"])) > 3 * ref]
                    for p in sorted(surges, key=lambda p: abs(float(p["net"])), reverse=True)[:3]:
                        net = float(p["net"])
                        add(p["date"], "foreign_flow_surge", "Positive" if net > 0 else "Negative", abs(net) / ref / 8,
                            f"Arus bersih asing Rp {_id(f'{net/1e9:,.1f}')} M, {_id(f'{abs(net)/ref:.1f}')}x rata-rata harian", "medium")
            except Exception:
                default_response["data_quality_flags"].append("foreign_flow_unavailable")

            if not events:
                default_response["as_of"] = str(df.index[-1].date())
                return default_response

            events.sort(key=lambda e: e["date"], reverse=True)
            last = df.index[-1]
            def weight(e):  # recent events count more; ~halves every 7 sessions
                age = max(0, len(df.loc[e["date"]:]) - 1)
                return e["strength"] * (0.9 ** age)
            pos = sum(weight(e) for e in events if e["direction"] == "Positive")
            neg = sum(weight(e) for e in events if e["direction"] == "Negative")
            net_direction = "Positive" if pos > neg * 1.2 else ("Negative" if neg > pos * 1.2 else "Mixed")
            return {
                "ticker": symbol,
                "as_of": str(last.date()),
                "lookback_sessions": LOOKBACK,
                "catalyst_score": round(min(1.0, pos + neg), 3),
                "net_direction": net_direction,
                "events": events,
                "data_quality_flags": default_response["data_quality_flags"],
            }
        except Exception as e:
            default_response["data_quality_flags"].append(f"error: {str(e)}")
            return default_response
