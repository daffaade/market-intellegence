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

    def _get_ohlcv(self, symbol: str, as_of: Optional[str] = None) -> pd.DataFrame:
        if self.data_loader and hasattr(self.data_loader, "get_historical_data"):
            df = self.data_loader.get_historical_data(symbol, period="1y")
            if df is not None and not df.empty:
                if as_of:
                    df = df.loc[:as_of]
                return df
        import yfinance as yf
        df = yf.download(f"{symbol}.JK", period="1y", progress=False, auto_adjust=False)
        if as_of and not df.empty:
            df = df.loc[:as_of]
        return df
        
    def _get_benchmark(self, as_of: Optional[str] = None) -> pd.DataFrame:
        if self.data_loader and hasattr(self.data_loader, "get_historical_data"):
            df = self.data_loader.get_historical_data("^JKSE", period="1y")
            if df is not None and not df.empty:
                if as_of:
                    df = df.loc[:as_of]
                return df
        import yfinance as yf
        df = yf.download("^JKSE", period="1y", progress=False, auto_adjust=False)
        if as_of and not df.empty:
            df = df.loc[:as_of]
        return df

    def analyze(self, symbol: str, as_of: Optional[str] = None) -> Dict[str, Any]:
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
            
            events = []
            
            # 1. Volume Spike
            vol_cfg = self.config["market_layer"]["volume_spike"]
            w = vol_cfg["window"]
            if len(df) >= w:
                vol_mean = float(np.squeeze(df['Volume'].rolling(w).mean().shift(1).iloc[-1]))
                vol_std = float(np.squeeze(df['Volume'].rolling(w).std().shift(1).iloc[-1]))
                curr_vol = float(np.squeeze(df['Volume'].iloc[-1]))
                
                if vol_std > 0:
                    z_score = (curr_vol - vol_mean) / vol_std
                    if z_score > vol_cfg["z_score_threshold"]:
                        # Determine direction based on price action
                        ret = float(np.squeeze(df['Close'].iloc[-1])) / float(np.squeeze(df['Close'].iloc[-2])) - 1
                        direction = "Positive" if ret > 0 else "Negative"
                        events.append({
                            "date": str(df.index[-1].date()),
                            "type": "volume_spike",
                            "layer": "market",
                            "direction": direction,
                            "strength": min(1.0, z_score / 5.0),
                            "confidence": "high",
                            "evidence": [f"Volume {curr_vol/vol_mean:.1f}x rata-rata {w} hari"]
                        })

            # 2. Breakout 52-week (252 days)
            brk_cfg = self.config["market_layer"]["breakout"]
            bw = brk_cfg["window"]
            if len(df) >= bw:
                high_52w = float(np.squeeze(df['High'].rolling(bw).max().shift(1).iloc[-1]))
                low_52w = float(np.squeeze(df['Low'].rolling(bw).min().shift(1).iloc[-1]))
                curr_close = float(np.squeeze(df['Close'].iloc[-1]))
                
                if curr_close > high_52w:
                    events.append({
                        "date": str(df.index[-1].date()),
                        "type": "breakout_high",
                        "layer": "market",
                        "direction": "Positive",
                        "strength": 0.8,
                        "confidence": "high",
                        "evidence": ["Harga menembus level tertinggi 52 minggu"]
                    })
                elif curr_close < low_52w:
                    events.append({
                        "date": str(df.index[-1].date()),
                        "type": "breakout_low",
                        "layer": "market",
                        "direction": "Negative",
                        "strength": 0.8,
                        "confidence": "high",
                        "evidence": ["Harga menembus level terendah 52 minggu"]
                    })
            
            # Combine Events
            if not events:
                return default_response
            
            # Calculate net direction and score
            pos_strength = sum(e["strength"] for e in events if e["direction"] == "Positive")
            neg_strength = sum(e["strength"] for e in events if e["direction"] == "Negative")
            
            total_strength = pos_strength + neg_strength
            catalyst_score = min(1.0, total_strength)
            
            if pos_strength > neg_strength:
                net_direction = "Positive"
            elif neg_strength > pos_strength:
                net_direction = "Negative"
            else:
                net_direction = "Mixed"

            return {
                "ticker": symbol,
                "as_of": str(df.index[-1].date()),
                "catalyst_score": round(catalyst_score, 3),
                "net_direction": net_direction,
                "events": events,
                "data_quality_flags": default_response["data_quality_flags"]
            }
            
        except Exception as e:
            default_response["data_quality_flags"].append(f"error: {str(e)}")
            return default_response

