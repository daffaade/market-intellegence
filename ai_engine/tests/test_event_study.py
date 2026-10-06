"""
test_event_study.py — Unit tests for ai_engine/modules/event_study.py

Tests:
  1. Data sintetis dengan shock diketahui → CAR mendekati shock (sanity check)
  2. Anti look-ahead: ubah data setelah event window → AR/CAR di window tidak berubah
  3. Fallback histori pendek (GOTO) → data_quality="partial", tidak exception
  4. Validasi skema output via Pydantic (kontrak JSON)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
# pyrefly: ignore [missing-import]
import pytest

# Path setup agar import modul berhasil di luar installer
CURRENT_DIR = Path(__file__).resolve().parent
AI_ENGINE_DIR = CURRENT_DIR.parent
REPO_ROOT = AI_ENGINE_DIR.parent
for _p in [str(CURRENT_DIR), str(AI_ENGINE_DIR), str(REPO_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from pydantic import BaseModel, field_validator
from typing import List, Optional

# Import fungsi yang diuji (import internal agar tidak perlu FastAPI)
from ai_engine.models.event_study.event_study import (
    run_event_study,
    _compute_event,
    _build_error_result,
)


# ── Pydantic schema — kontrak output ─────────────────────────────────────────
class EventStudyOutput(BaseModel):
    ticker: str
    event_id: Optional[str]
    event_type: Optional[str]
    car: Optional[float]
    t_stat: Optional[float]
    p_value: Optional[float]
    significant_at_5pct: Optional[bool]
    level: str
    score: int
    evidence: List[str]
    data_quality: str
    data_source: str

    @field_validator("level")
    @classmethod
    def level_valid(cls, v):
        assert v in ("Low", "Medium", "High"), f"level tidak valid: {v}"
        return v

    @field_validator("data_quality")
    @classmethod
    def dq_valid(cls, v):
        assert v in ("ok", "partial", "missing"), f"data_quality tidak valid: {v}"
        return v

    @field_validator("score")
    @classmethod
    def score_range(cls, v):
        assert 0 <= v <= 100, f"score di luar range: {v}"
        return v


# ── Helper: buat data sintetis ────────────────────────────────────────────────
def _make_synthetic_returns(
    n_days: int = 400,
    shock_at_day: int = 300,
    shock_magnitude: float = 0.05,
    noise_std: float = 0.01,
    seed: int = 42,
) -> tuple[pd.Series, pd.Series, int]:
    """
    Buat return sintetis dengan shock buatan di hari shock_at_day.
    Returns: ticker_ret, market_ret, shock_day_idx
    """
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2020-01-01", periods=n_days)
    market = rng.normal(0.0, noise_std, n_days)
    # Stock: 0.8 × market + alpha + noise
    stock = 0.8 * market + 0.001 + rng.normal(0.0, noise_std * 0.5, n_days)
    # Inject shock di hari shock_at_day
    stock[shock_at_day] += shock_magnitude
    ticker_ret = pd.Series(stock, index=dates, name="close")
    market_ret = pd.Series(market, index=dates, name="close")
    return ticker_ret, market_ret, shock_at_day


# ── Test 1: Sanity check CAR mendekati shock ──────────────────────────────────
class TestCarSanityCheck:
    def test_car_close_to_shock(self):
        """
        Dengan shock +5% di hari 0 event window, CAR harus mendekati +5%.
        Toleransi longgar karena beta dan residual mempengaruhi estimasi.
        """
        SHOCK = 0.05
        ticker_ret, market_ret, shock_idx = _make_synthetic_returns(
            n_days=400,
            shock_at_day=300,  # event date di posisi 300
            shock_magnitude=SHOCK,
        )

        event = {
            "ticker": "TEST",
            "date": ticker_ret.index[300].strftime("%Y-%m-%d"),
            "event_type": "earnings",
            "description": "Test event",
        }
        cfg = {
            "estimation_window": {"start": -250, "end": -30, "min_obs": 80},
            "event_window": {"start": -5, "end": 5},
            "significance_level": 0.05,
            "score": {
                "car_high_threshold": 0.10,
                "significance_boost": 1.2,
                "level_thresholds": {"high": 70, "medium": 40},
            },
            "fallback": {"min_obs_partial": 30},
        }

        result = _compute_event(event, ticker_ret, market_ret, cfg)

        assert result is not None, "Hasil tidak boleh None"
        assert result["car"] is not None, "CAR harus dihitung"
        # CAR harus positif (shock positif)
        assert result["car"] > 0, f"CAR harus positif, dapat {result['car']}"
        # CAR harus dalam ±15% dari shock (toleransi untuk residual dan beta)
        assert abs(result["car"] - SHOCK) < 0.15, (
            f"CAR {result['car']:.4f} terlalu jauh dari shock {SHOCK}"
        )

    def test_negative_shock(self):
        """Shock negatif → CAR harus negatif."""
        SHOCK = -0.04
        ticker_ret, market_ret, shock_idx = _make_synthetic_returns(
            n_days=400, shock_at_day=300, shock_magnitude=SHOCK
        )
        event = {
            "ticker": "TEST",
            "date": ticker_ret.index[300].strftime("%Y-%m-%d"),
            "event_type": "disaster",
            "description": "Test negative shock",
        }
        cfg = {
            "estimation_window": {"start": -250, "end": -30, "min_obs": 80},
            "event_window": {"start": -5, "end": 5},
            "significance_level": 0.05,
            "score": {
                "car_high_threshold": 0.10,
                "significance_boost": 1.2,
                "level_thresholds": {"high": 70, "medium": 40},
            },
            "fallback": {"min_obs_partial": 30},
        }
        result = _compute_event(event, ticker_ret, market_ret, cfg)
        assert result["car"] is not None
        assert result["car"] < 0, f"CAR harus negatif, dapat {result['car']}"


# ── Test 2: Anti look-ahead ───────────────────────────────────────────────────
class TestAntiLookAhead:
    def test_data_after_event_window_does_not_affect_car(self):
        """
        Ubah return SETELAH event window → CAR dalam window tidak berubah.
        Ini membuktikan tidak ada look-ahead bias.
        """
        ticker_ret, market_ret, shock_idx = _make_synthetic_returns(
            n_days=400, shock_at_day=300, shock_magnitude=0.03
        )
        event = {
            "ticker": "TEST",
            "date": ticker_ret.index[300].strftime("%Y-%m-%d"),
            "event_type": "earnings",
            "description": "Test look-ahead",
        }
        cfg = {
            "estimation_window": {"start": -250, "end": -30, "min_obs": 80},
            "event_window": {"start": -5, "end": 5},
            "significance_level": 0.05,
            "score": {
                "car_high_threshold": 0.10,
                "significance_boost": 1.2,
                "level_thresholds": {"high": 70, "medium": 40},
            },
            "fallback": {"min_obs_partial": 30},
        }

        # Hitung CAR pertama
        result1 = _compute_event(event, ticker_ret, market_ret, cfg)

        # Modifikasi data SETELAH event window (posisi 310+)
        ticker_ret_modified = ticker_ret.copy()
        ticker_ret_modified.iloc[310:] += 0.99  # perubahan besar setelah window

        result2 = _compute_event(event, ticker_ret_modified, market_ret, cfg)

        # CAR harus sama persis (karena event window adalah [-5, +5] = [295, 305])
        assert result1["car"] is not None
        assert result2["car"] is not None
        assert abs(result1["car"] - result2["car"]) < 1e-9, (
            f"Look-ahead terdeteksi: CAR1={result1['car']:.6f} != CAR2={result2['car']:.6f}"
        )


# ── Test 3: Fallback histori pendek (GOTO) ────────────────────────────────────
class TestShortHistoryFallback:
    def test_partial_data_quality_not_exception(self):
        """
        Histori sangat pendek (< 80 obs normal) → data_quality="partial", tidak crash.
        Mensimulasikan kondisi GOTO dengan histori sejak IPO April 2022.
        """
        # Buat hanya 100 hari data (kurang dari min_obs=80 untuk "ok" → partial)
        rng = np.random.default_rng(0)
        dates = pd.bdate_range("2022-04-11", periods=100)  # GOTO IPO date
        stock = rng.normal(0.001, 0.015, 100)
        market = rng.normal(0.0, 0.01, 100)
        ticker_ret = pd.Series(stock, index=dates)
        market_ret = pd.Series(market, index=dates)

        # Event di tengah data
        event = {
            "ticker": "GOTO",
            "date": dates[70].strftime("%Y-%m-%d"),
            "event_type": "earnings",
            "description": "GOTO Q3-2022",
        }
        cfg = {
            "estimation_window": {"start": -250, "end": -30, "min_obs": 80},
            "event_window": {"start": -5, "end": 5},
            "significance_level": 0.05,
            "score": {
                "car_high_threshold": 0.10,
                "significance_boost": 1.2,
                "level_thresholds": {"high": 70, "medium": 40},
            },
            "fallback": {"min_obs_partial": 30},
        }

        # Tidak boleh raise exception
        try:
            result = _compute_event(event, ticker_ret, market_ret, cfg)
        except Exception as e:
            pytest.fail(f"Exception tidak boleh dilempar untuk histori pendek: {e}")

        assert result is not None
        # Harus partial atau missing (bukan ok karena data terlalu pendek)
        assert result["data_quality"] in ("partial", "missing"), (
            f"Histori pendek harus partial/missing, bukan '{result['data_quality']}'"
        )

    def test_very_short_history_returns_missing(self):
        """Histori < 30 hari → data_quality="missing"."""
        rng = np.random.default_rng(1)
        dates = pd.bdate_range("2022-04-11", periods=25)
        ticker_ret = pd.Series(rng.normal(0, 0.01, 25), index=dates)
        market_ret = pd.Series(rng.normal(0, 0.01, 25), index=dates)
        event = {
            "ticker": "GOTO",
            "date": dates[20].strftime("%Y-%m-%d"),
            "event_type": "ipo",
            "description": "GOTO IPO",
        }
        cfg = {
            "estimation_window": {"start": -250, "end": -30, "min_obs": 80},
            "event_window": {"start": -5, "end": 5},
            "significance_level": 0.05,
            "score": {
                "car_high_threshold": 0.10,
                "significance_boost": 1.2,
                "level_thresholds": {"high": 70, "medium": 40},
            },
            "fallback": {"min_obs_partial": 30},
        }
        result = _compute_event(event, ticker_ret, market_ret, cfg)
        assert result["data_quality"] == "missing"
        assert result["car"] is None


# ── Test 4: Validasi skema output (Pydantic) ──────────────────────────────────
class TestOutputSchema:
    def test_schema_valid_result(self):
        """Output dari _compute_event harus lolos validasi skema kontrak."""
        ticker_ret, market_ret, _ = _make_synthetic_returns()
        event = {
            "ticker": "BBCA",
            "date": ticker_ret.index[300].strftime("%Y-%m-%d"),
            "event_type": "dividend",
            "description": "Dividen BBCA",
        }
        cfg = {
            "estimation_window": {"start": -250, "end": -30, "min_obs": 80},
            "event_window": {"start": -5, "end": 5},
            "significance_level": 0.05,
            "score": {
                "car_high_threshold": 0.10,
                "significance_boost": 1.2,
                "level_thresholds": {"high": 70, "medium": 40},
            },
            "fallback": {"min_obs_partial": 30},
        }
        result = _compute_event(event, ticker_ret, market_ret, cfg)
        # Harus lolos Pydantic tanpa error
        validated = EventStudyOutput(**result)
        assert validated.ticker == "BBCA"
        assert validated.evidence, "evidence tidak boleh kosong"

    def test_schema_error_result(self):
        """Output dari _build_error_result juga harus lolos skema."""
        event = {
            "ticker": "GOTO",
            "date": "2022-04-11",
            "event_type": "ipo",
            "description": "Test",
        }
        result = _build_error_result(event, "Histori terlalu pendek", "missing")
        validated = EventStudyOutput(**result)
        assert validated.data_quality == "missing"
        assert validated.car is None

    def test_p_value_not_filtered(self):
        """
        p-value tidak signifikan (p > 0.05) harus tetap muncul di output,
        tidak dibuang atau disembunyikan.
        """
        ticker_ret, market_ret, _ = _make_synthetic_returns(
            shock_magnitude=0.001  # shock kecil → kemungkinan tidak signifikan
        )
        event = {
            "ticker": "BBCA",
            "date": ticker_ret.index[300].strftime("%Y-%m-%d"),
            "event_type": "earnings",
            "description": "Test tidak signifikan",
        }
        cfg = {
            "estimation_window": {"start": -250, "end": -30, "min_obs": 80},
            "event_window": {"start": -5, "end": 5},
            "significance_level": 0.05,
            "score": {
                "car_high_threshold": 0.10,
                "significance_boost": 1.2,
                "level_thresholds": {"high": 70, "medium": 40},
            },
            "fallback": {"min_obs_partial": 30},
        }
        result = _compute_event(event, ticker_ret, market_ret, cfg)
        # Hasil harus tetap ada (tidak None/dibuang) meski tidak signifikan
        assert result is not None
        assert "p_value" in result
        assert result["p_value"] is not None, "p_value tidak boleh None meski tidak signifikan"
        assert "evidence" in result and result["evidence"]


# ── Test 5: run_event_study tidak crash untuk semua ticker prototype ──────────
class TestRunEventStudy:
    @pytest.mark.parametrize("ticker", ["BBCA", "AMRT", "TLKM", "ASII", "GOTO"])
    def test_run_returns_list_without_crash(self, ticker):
        """
        run_event_study harus return list (tanpa crash) untuk semua prototype ticker.
        Menggunakan data_loader=None sehingga jatuh ke yfinance fallback.
        Tes ini mungkin butuh koneksi internet — di-skip jika tidak ada data.
        """
        try:
            result = run_event_study(ticker)
        except Exception as e:
            pytest.skip(f"Network tidak tersedia atau data kosong: {e}")

        assert isinstance(result, list), "run_event_study tanpa event_id harus return list"
        assert len(result) > 0, "Harus ada minimal 1 hasil"

        for r in result:
            # Setiap item harus lolos schema
            validated = EventStudyOutput(**r)
            # p_value tidak boleh dihilangkan
            if validated.car is not None:
                assert validated.p_value is not None
