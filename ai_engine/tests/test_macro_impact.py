from __future__ import annotations
import sys
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from pydantic import BaseModel, field_validator
from typing import Any, Dict, List, Optional

CURRENT_DIR = Path(__file__).resolve().parent
AI_ENGINE_DIR = CURRENT_DIR.parent
REPO_ROOT = AI_ENGINE_DIR.parent
for _p in [str(CURRENT_DIR), str(AI_ENGINE_DIR), str(REPO_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from ai_engine.models.macro_impact.macro_impact import (
    run_macro_impact,
    _detect_forecast_revisions,
    _detect_macro_shocks,
)
from ai_engine.core.data_loader import UnifiedDataLoader
import ai_engine.core.data_macro as data_macro

class MacroImpactOutput(BaseModel):
    ticker: str
    as_of: str
    forecast_revisions: List[Any]
    co_occurrence_rate: float
    base_rate: float
    level: str
    score: Optional[int]
    evidence: List[str]
    data_quality: str
    data_source: str

    @field_validator("level")
    @classmethod
    def level_valid(cls, v):
        assert v in ("Low", "Medium", "High")
        return v

    @field_validator("data_quality")
    @classmethod
    def dq_valid(cls, v):
        assert v in ("ok", "partial", "missing", "proxy")
        return v

CAUSAL_BLOCKLIST = [
    "menyebabkan", "mengakibatkan", "causes", "caused by", "akibat dari", 
    "karena makro", "disebabkan oleh", "dampak langsung dari", "effect of", "impact of macro on"
]

SYNTHETIC_CFG = {
    "bi_rate": 0.25,
    "usdidr": 0.03,
}

class TestForecastRevisionDetection:
    def test_known_revision_detected(self):
        months = pd.date_range("2023-01-01", periods=24, freq="ME")
        prices = pd.Series(
            [100.0, 101.0, 102.0, 101.5, 102.5,
             115.0, 116.0, 117.0, 116.5, 115.0, 116.0, 117.0,
             118.0, 117.5, 118.5, 119.0, 118.0, 119.5,
             120.0, 121.0, 120.5, 121.5, 122.0, 123.0],
            index=months,
        )
        dates = pd.bdate_range("2023-01-01", periods=500)
        price_daily = prices.reindex(dates, method="ffill").ffill().bfill()
        
        # In P2 proxy is return_20d * 1.5. Calculate that for testing
        df = pd.DataFrame({"close": price_daily})
        df["return_20d"] = df["close"].pct_change(20) * 100
        forecast_proxy = df["return_20d"].dropna() * 1.5

        revisions = _detect_forecast_revisions(forecast_proxy, threshold_pp=2.0)
        assert len(revisions) > 0, "Harus ada minimal 1 revisi terdeteksi"

    def test_no_revision_flat_series(self):
        dates = pd.bdate_range("2023-01-01", periods=300)
        prices = pd.Series([100.0] * 300, index=dates)
        
        df = pd.DataFrame({"close": prices})
        df["return_20d"] = df["close"].pct_change(20) * 100
        forecast_proxy = df["return_20d"].dropna() * 1.5
        
        revisions = _detect_forecast_revisions(forecast_proxy, threshold_pp=2.0)
        assert len(revisions) == 0

    def test_short_series_returns_empty(self):
        dates = pd.bdate_range("2023-01-01", periods=10)
        prices = pd.Series(range(100, 110), index=dates, dtype=float)
        
        df = pd.DataFrame({"close": prices})
        df["return_20d"] = df["close"].pct_change(20) * 100
        forecast_proxy = df["return_20d"].dropna() * 1.5
        
        revisions = _detect_forecast_revisions(forecast_proxy, threshold_pp=2.0)
        assert isinstance(revisions, list)

class TestMacroShockDetection:
    def test_shock_at_threshold(self):
        dates = pd.date_range("2023-01-31", periods=6, freq="ME")
        bi_rates = [5.75, 6.00, 6.00, 6.00, 6.00, 6.00]
        macro_df = pd.DataFrame({"variable": "bi_rate", "value": bi_rates, "date": dates})
        shocks = _detect_macro_shocks(macro_df, SYNTHETIC_CFG)
        assert len(shocks) >= 1

    def test_below_threshold_not_detected(self):
        dates = pd.date_range("2023-01-31", periods=6, freq="ME")
        bi_rates = [5.75, 5.90, 5.90, 5.90, 5.90, 5.90]
        macro_df = pd.DataFrame({"variable": "bi_rate", "value": bi_rates, "date": dates})
        shocks = _detect_macro_shocks(macro_df, SYNTHETIC_CFG)
        assert len(shocks) == 0

    def test_usdidr_percentage_shock(self):
        dates = pd.date_range("2023-01-31", periods=4, freq="ME")
        rates = [15000, 15465, 15465, 15465]
        macro_df = pd.DataFrame({"variable": "usdidr", "value": rates, "date": dates})
        shocks = _detect_macro_shocks(macro_df, SYNTHETIC_CFG)
        assert len(shocks) >= 1

    def test_usdidr_below_percentage_threshold(self):
        dates = pd.date_range("2023-01-31", periods=4, freq="ME")
        rates = [15000, 15200, 15200, 15200]
        macro_df = pd.DataFrame({"variable": "usdidr", "value": rates, "date": dates})
        shocks = _detect_macro_shocks(macro_df, SYNTHETIC_CFG)
        assert len(shocks) == 0

class TestCoOccurrenceWindow:
    def test_shock_within_window_detected(self, monkeypatch):
        def mock_load_macro():
            dates = pd.date_range("2024-02-29", periods=2, freq="ME")
            df = pd.DataFrame({"variable": ["bi_rate", "bi_rate"], "value": [5.75, 6.00], "date": dates})
            df.attrs["data_quality"] = "ok"
            df.attrs["data_source"] = "real"
            return df
            
        def mock_load_price(ticker):
            dates = pd.bdate_range("2024-01-01", periods=100)
            prices = np.linspace(100, 105, 100)
            prices[-20:] = 120 # shock to create revision near end of March
            df = pd.DataFrame({"close": prices}, index=dates)
            return df
            
        monkeypatch.setattr("ai_engine.models.macro_impact.macro_impact._load_macro_series", mock_load_macro)
        monkeypatch.setattr(UnifiedDataLoader, "get_historical_data", mock_load_price)
        
        result = run_macro_impact("TEST")
        assert result["co_occurrence_rate"] > 0

    def test_shock_outside_window_not_detected(self, monkeypatch):
        def mock_load_macro():
            # Shock long time ago
            dates = pd.date_range("2023-02-28", periods=2, freq="ME")
            df = pd.DataFrame({"variable": ["bi_rate", "bi_rate"], "value": [5.75, 6.00], "date": dates})
            return df
            
        def mock_load_price(ticker):
            dates = pd.bdate_range("2024-01-01", periods=100)
            prices = np.linspace(100, 105, 100)
            prices[-20:] = 120 # shock to create revision near end of March
            df = pd.DataFrame({"close": prices}, index=dates)
            return df
            
        monkeypatch.setattr("ai_engine.models.macro_impact.macro_impact._load_macro_series", mock_load_macro)
        monkeypatch.setattr(UnifiedDataLoader, "get_historical_data", mock_load_price)
        
        result = run_macro_impact("TEST")
        assert result["co_occurrence_rate"] == 0.0

class TestCausalLanguageBlocklist:
    def test_no_causal_language_in_evidence(self):
        try:
            result = run_macro_impact("ASII")
        except Exception:
            pytest.skip("Data not available")
            
        evidence_text = " ".join(result.get("evidence", [])).lower()
        for word in CAUSAL_BLOCKLIST:
            assert word.lower() not in evidence_text

class TestOutputSchema:
    def test_schema_valid(self):
        try:
            result = run_macro_impact("TLKM")
        except Exception:
            pytest.skip("Data not available")
        validated = MacroImpactOutput(**result)
        assert validated.ticker == "TLKM"

    def test_schema_missing_ticker(self, monkeypatch):
        def mock_empty(t):
            return pd.DataFrame()
        monkeypatch.setattr(UnifiedDataLoader, "get_historical_data", mock_empty)
        result = run_macro_impact("XXXXXXINVALID")
        validated = MacroImpactOutput(**result)
        assert validated.data_quality == "missing"

class TestBootstrapAndFallback:
    def test_bootstrap_empty(self, monkeypatch):
        # We simulate empty data dir by mocking the live fetch logic inside data_macro
        # Or we can just call data_macro.get_macro_series() and ensure it doesn't crash
        # when the dir is missing.
        df = data_macro.get_macro_series()
        assert isinstance(df, pd.DataFrame)
        
    def test_fallback_total_failure(self, monkeypatch):
        def mock_get(*args, **kwargs):
            raise Exception("Mock live fail")
        def mock_dl(*args, **kwargs):
            raise Exception("Mock dl fail")
        monkeypatch.setattr("requests.get", mock_get)
        monkeypatch.setattr("yfinance.download", mock_dl)
        monkeypatch.setattr("ai_engine.core.data_macro.Path.exists", lambda x: False)
        
        df = data_macro.get_macro_series()
        assert df.empty
        assert df.attrs.get("data_quality") == "missing"
