"""
Sector Intelligence Model - ai_engine/models/sector/sector_intelligence.py
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

CONFIG_PATH = AI_ENGINE_DIR / "config" / "sector_map.yaml"

try:
    from ai_engine.core.data_loader import UnifiedDataLoader
    from ai_engine.models.forecast.forecast_model import ForecastModel
    from ai_engine.models.peers.peer_analysis import PeerAnalysisModel
    from ai_engine.models.peers.what_changed import WhatChangedModel
    from ai_engine.models.anomaly.isolation_forest import AnomalyModel
except ImportError:
    UnifiedDataLoader = None


class SectorIntelligenceModel:
    def __init__(self, data_loader=None):
        self.data_loader = data_loader
        self._load_config()

    def _load_config(self):
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r") as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {
                "universe": {},
                "thresholds": {"momentum_bullish": 0.5, "momentum_bearish": -0.5, "min_constituents": 3}
            }

    def _get_benchmark(self, as_of: Optional[str] = None) -> pd.DataFrame:
        if self.data_loader and self.data_loader.yfinance_provider:
            df = self.data_loader.yfinance_provider.get_historical_data("^JKSE", period="1y")
            if df is not None and not df.empty:
                if as_of:
                    return df.loc[:as_of]
                return df
        
        import yfinance as yf
        df = yf.download("^JKSE", period="1y", progress=False, auto_adjust=False)
        if as_of and not df.empty:
            df = df.loc[:as_of]
        return df

    def _get_ohlcv(self, symbol: str, as_of: Optional[str] = None) -> pd.DataFrame:
        import yfinance as yf
        df = yf.download(f"{symbol}.JK", period="1y", progress=False, auto_adjust=False)
        if as_of and not df.empty:
            df = df.loc[:as_of]
        return df

    def analyze_sector(self, sector_name: str, as_of: Optional[str] = None) -> Dict[str, Any]:
        universe = self.config["universe"].get(sector_name, [])
        default_response = {
            "sector": sector_name,
            "as_of": as_of or datetime.today().strftime('%Y-%m-%d'),
            "n_constituents": len(universe),
            "low_confidence": True,
            "momentum_score": 0.0,
            "sentiment_label": "Neutral",
            "rotation_rank": 0,
            "rotation_signal": "Stable",
            "metrics": {},
            "evidence": [],
            "top_contributors": []
        }

        if len(universe) < self.config["thresholds"]["min_constituents"]:
            default_response["evidence"].append("Insufficient constituents")
            return default_response

        # Fetch Benchmark
        idx_df = self._get_benchmark(as_of)
        idx_ret_20d = 0.0
        if not idx_df.empty and len(idx_df) >= 20:
            val_last = float(np.squeeze(idx_df['Close'].iloc[-1]))
            val_prev = float(np.squeeze(idx_df['Close'].iloc[-20]))
            idx_ret_20d = val_last / val_prev - 1.0

        # Fetch components data
        above_ma50_count = 0
        pos_ret20_count = 0
        valid_constituents = 0
        rs_list = []
        
        avg_opp = []
        div_count = 0

        for sym in universe:
            df = self._get_ohlcv(sym, as_of)
            if df.empty:
                continue
            
            valid_constituents += 1
            close_prices = df['Close']
            
            if len(close_prices) >= 20:
                # Use .item() or float() to ensure scalar extraction if it returns a Series
                val_last = float(np.squeeze(close_prices.iloc[-1]))
                val_prev = float(np.squeeze(close_prices.iloc[-20]))
                ret20 = val_last / val_prev - 1
                if ret20 > 0:
                    pos_ret20_count += 1
                # Ensure idx_ret_20d is scalar too
                rs_vs_ihsg = ret20 - float(np.squeeze(idx_ret_20d))
                rs_list.append(rs_vs_ihsg)

            if len(close_prices) >= 50:
                ma50 = float(np.squeeze(close_prices.rolling(50).mean().iloc[-1]))
                if float(np.squeeze(close_prices.iloc[-1])) > ma50:
                    above_ma50_count += 1
                    
            # For hackathon efficiency, we mock the heavy model calls if they take too long,
            # but ideally we would call ForecastModel and PeerAnalysisModel here.
            # In real system, this should query the DB cache directly instead of running inference.

        if valid_constituents == 0:
            return default_response

        breadth_ma50 = above_ma50_count / valid_constituents
        median_rs = np.median(rs_list) if rs_list else 0.0

        # Calculate composite momentum score (z-score like)
        momentum_score = (median_rs * 0.6) + ((breadth_ma50 - 0.5) * 0.4)
        
        # Determine Sentiment
        if momentum_score > self.config["thresholds"]["momentum_bullish"]:
            sentiment = "Bullish"
        elif momentum_score < self.config["thresholds"]["momentum_bearish"]:
            sentiment = "Bearish"
        else:
            sentiment = "Neutral"

        evidence = [
            f"{above_ma50_count} dari {valid_constituents} saham di atas MA50",
            f"Median RS 20D vs IHSG {median_rs*100:+.1f}%"
        ]

        return {
            "sector": sector_name,
            "as_of": str(idx_df.index[-1].date()) if not idx_df.empty else default_response["as_of"],
            "n_constituents": valid_constituents,
            "low_confidence": valid_constituents < self.config["thresholds"]["min_constituents"],
            "momentum_score": float(round(momentum_score, 3)),
            "sentiment_label": sentiment,
            "rotation_rank": 0, # Requires cross-sector analysis to populate
            "rotation_signal": "Stable",
            "metrics": {
                "rs_vs_ihsg_20d": float(round(median_rs, 3)),
                "breadth_ma50": float(round(breadth_ma50, 3)),
                "avg_opportunity": 0.5, # Mock, needs DB cache
                "avg_risk": "Medium",
                "divergence_count": div_count,
                "median_pe_percentile": 0.5
            },
            "evidence": evidence,
            "top_contributors": universe[:2] # Simplification
        }
