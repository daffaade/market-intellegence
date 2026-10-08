"""
Smart Money Model - ai_engine/models/smart_money/smart_money_model.py
"""
import sys
import yaml
import math
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

try:
    from ai_engine.core.data_loader import UnifiedDataLoader
except ImportError:
    UnifiedDataLoader = None

CONFIG_PATH = AI_ENGINE_DIR / "config" / "smart_money.yaml"


class SmartMoneyModel:
    def __init__(self, data_loader=None):
        self.data_loader = data_loader
        self._load_config()

    def _load_config(self):
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r") as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {
                "windows": {"short": 5, "medium": 20, "long": 60},
                "thresholds": {"accumulation": 0.25, "distribution": -0.25},
                "weights": {
                    "actor_type": {"insider": 1.0, "foreign": 0.8, "institution": 0.5, "retail-unknown": 0.1},
                    "components": {"transaction_flow": 0.3, "cmf": 0.3, "obv_trend": 0.2, "price_flow_divergence": 0.2}
                }
            }

    def _get_ohlcv(self, symbol: str) -> pd.DataFrame:
        if self.data_loader and hasattr(self.data_loader, "get_historical_data"):
            df = self.data_loader.get_historical_data(symbol, period="1y")
            if df is not None and not df.empty:
                return df
        # Fallback to yfinance directly if no data_loader
        import yfinance as yf
        df = yf.download(f"{symbol}.JK", period="1y", progress=False, auto_adjust=False)
        return df

    def _get_transactions(self, symbol: str) -> pd.DataFrame:
        if self.data_loader:
            try:
                res = self.data_loader.get_institutional_transactions(symbol, period="1y")
                val = res.get("value")
                if isinstance(val, list) and val:
                    return pd.DataFrame(val)
                elif isinstance(val, dict) and val:
                    return pd.DataFrame([val])
            except Exception:
                pass
        return pd.DataFrame()

    def _compute_obv(self, df: pd.DataFrame) -> pd.Series:
        close = df['Close'].squeeze()
        volume = df['Volume'].squeeze()
        obv = np.where(close > close.shift(1), volume,
               np.where(close < close.shift(1), -volume, 0))
        return pd.Series(np.squeeze(obv), index=df.index).cumsum()

    def _compute_cmf(self, df: pd.DataFrame, window: int = 20) -> pd.Series:
        # Chaikin Money Flow
        high = df['High'].squeeze()
        low = df['Low'].squeeze()
        close = df['Close'].squeeze()
        volume = df['Volume'].squeeze()
        
        mf_multiplier = np.where(high != low,
                                 ((close - low) - (high - close)) / (high - low).replace(0, np.nan),
                                 0)
        mf_volume = mf_multiplier * volume
        cmf = pd.Series(np.squeeze(mf_volume), index=df.index).rolling(window).sum() / volume.rolling(window).sum()
        return cmf

    def analyze(self, symbol: str, as_of: Optional[str] = None) -> Dict[str, Any]:
        """
        Main entry point for analyzing smart money.
        as_of is to support anti-look-ahead testing.
        """
        default_response = {
            "ticker": symbol,
            "as_of": as_of or datetime.today().strftime('%Y-%m-%d'),
            "state": "Neutral",
            "score": 0.0,
            "components": {"transaction_flow": 0.0, "cmf": 0.0, "obv_trend": 0.0, "price_flow_divergence": 0.0},
            "confidence": "low",
            "data_source": "proxy",
            "evidence": [],
            "data_quality_flags": []
        }

        try:
            df = self._get_ohlcv(symbol)
            if df is None or df.empty:
                default_response["data_quality_flags"].append("empty_price_data")
                return default_response
            
            # Anti-look-ahead
            if as_of:
                df = df.loc[:as_of]
                if df.empty:
                    default_response["data_quality_flags"].append(f"no_data_before_{as_of}")
                    return default_response

            if len(df) < self.config['windows']['long']:
                default_response["data_quality_flags"].append("insufficient_data_history")
            
            evidence = []
            
            # 1. OBV and Trend
            df['OBV'] = self._compute_obv(df)
            short_w = self.config['windows']['short']
            if len(df) >= short_w:
                recent_obv = df['OBV'].iloc[-short_w:]
                obv_up_days = (recent_obv.diff() > 0).sum()
                obv_score = (obv_up_days / short_w) * 2 - 1 # Normalize to -1..1
                evidence.append(f"OBV naik {obv_up_days} dari {short_w} hari terakhir")
            else:
                obv_score = 0.0

            # 2. CMF
            cmf_w = self.config['windows']['medium']
            df['CMF'] = self._compute_cmf(df, window=cmf_w)
            if len(df) >= cmf_w and not pd.isna(df['CMF'].iloc[-1]):
                cmf_val = df['CMF'].iloc[-1]
                cmf_score = max(-1.0, min(1.0, cmf_val * 2)) # Approx normalize
                evidence.append(f"CMF({cmf_w})={cmf_val:+.2f}")
            else:
                cmf_score = 0.0

            # 3. Price-Flow Divergence
            div_score = 0.0
            if len(df) >= cmf_w:
                price_ret = float(np.squeeze(df['Close'].iloc[-1])) / float(np.squeeze(df['Close'].iloc[-cmf_w])) - 1
                obv_ret = float(np.squeeze(df['OBV'].iloc[-1])) / max(abs(float(np.squeeze(df['OBV'].iloc[-cmf_w]))), 1) - 1
                if price_ret < 0 and obv_ret > 0:
                    div_score = 1.0
                    evidence.append("Hidden accumulation (harga turun, OBV naik)")
                elif price_ret > 0 and obv_ret < 0:
                    div_score = -1.0
                    evidence.append("Hidden distribution (harga naik, OBV turun)")
            
            # 4. Transaction flow: net foreign flow over the medium window, as a share
            # of the stock's turnover (Sectors foreign-flow, read from cache).
            trans_score, has_flow = 0.0, False
            try:
                from data_processing.data_sectors.market_series import get_foreign_flow
                ff = get_foreign_flow(symbol.upper().replace(".JK", ""))
                pts = [p for p in (ff or {}).get("points", []) if p.get("net") is not None]
                if as_of:
                    pts = [p for p in pts if p["date"] <= as_of]
                if len(pts) >= cmf_w:
                    net = sum(float(p["net"]) for p in pts[-cmf_w:])
                    close = df['Close'].squeeze() if hasattr(df['Close'], 'squeeze') else df['Close']
                    vol = df['Volume'].squeeze() if hasattr(df['Volume'], 'squeeze') else df['Volume']
                    turnover = float((close * vol).iloc[-cmf_w:].sum())
                    if turnover > 0:
                        share = net / turnover
                        trans_score = max(-1.0, min(1.0, share / 0.10))
                        has_flow = True
                        evidence.append(
                            f"Arus bersih asing {cmf_w} sesi Rp {net / 1e9:,.1f} M ({share * 100:+.1f}% nilai transaksi)"
                            .replace(",", "_").replace(".", ",").replace("_", ".")
                        )
            except Exception:
                default_response["data_quality_flags"].append("foreign_flow_unavailable")

            # Composite Score. Without flow data its weight is redistributed instead of
            # counting as a neutral 0 that drags every score toward "Neutral".
            weights = dict(self.config['weights']['components'])
            if not has_flow:
                weights['transaction_flow'] = 0.0
            total_weight = sum(weights.values())

            final_score = (
                (trans_score * weights['transaction_flow']) +
                (cmf_score * weights['cmf']) +
                (obv_score * weights['obv_trend']) +
                (div_score * weights['price_flow_divergence'])
            ) / total_weight

            # State
            if final_score > self.config['thresholds']['accumulation']:
                state = "Accumulation"
            elif final_score < self.config['thresholds']['distribution']:
                state = "Distribution"
            else:
                state = "Neutral"

            return {
                "ticker": symbol,
                "as_of": str(df.index[-1].date()),
                "state": state,
                "score": float(round(final_score, 3)),
                "components": {
                    "transaction_flow": float(round(trans_score, 3)),
                    "cmf": float(round(cmf_score, 3)),
                    "obv_trend": float(round(obv_score, 3)),
                    "price_flow_divergence": float(round(div_score, 3))
                },
                "confidence": ("high" if has_flow else "medium") if len(df) >= 60 else "low",
                "data_source": "sectors_foreign_flow+price_volume" if has_flow else "price_volume_proxy",
                "evidence": evidence,
                "data_quality_flags": default_response["data_quality_flags"]
            }

        except Exception as e:
            default_response["data_quality_flags"].append(f"error: {str(e)}")
            return default_response

