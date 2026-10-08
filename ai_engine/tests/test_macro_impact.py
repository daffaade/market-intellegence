"""Macro sensitivity on synthetic weekly data: no network."""
import numpy as np
import pandas as pd

import ai_engine.models.macro_impact.macro_impact as M

CAUSAL_BLOCKLIST = ["menyebabkan", "mengakibatkan", "akibat", "disebabkan", "dampak langsung", "karena"]


def _setup(monkeypatch, stock_beta_on_gold: float):
    rng = np.random.default_rng(1)
    idx = pd.date_range("2024-10-04", periods=105, freq="W-FRI")
    rets = {t: rng.normal(0, 0.02, len(idx)) for _, t, _, _ in M.FACTORS}
    factors = pd.DataFrame({t: 100 * np.cumprod(1 + r) for t, r in rets.items()}, index=idx)
    stock_ret = 0.6 * rets["^JKSE"] + stock_beta_on_gold * rets["GC=F"] + rng.normal(0, 0.01, len(idx))
    stock = pd.DataFrame({"TEST.JK": 1000 * np.cumprod(1 + stock_ret)}, index=idx)
    monkeypatch.setattr(M, "_factor_closes", lambda: factors)
    monkeypatch.setattr(M, "_weekly_closes", lambda tickers: stock)


def test_recovers_gold_exposure(monkeypatch):
    _setup(monkeypatch, stock_beta_on_gold=0.9)
    res = M.run_macro_impact("TEST")
    by = {s["key"]: s for s in res["sensitivities"]}
    assert by["gold"]["significant"] and 0.7 < by["gold"]["beta"] < 1.1
    assert by["ihsg"]["significant"]
    assert not by["brent"]["significant"]
    assert res["dominant_macro"] == "Emas"
    assert by["brent"]["implied_move_1m_pct"] is None  # only significant links imply a move


def test_language_is_correlational(monkeypatch):
    _setup(monkeypatch, stock_beta_on_gold=0.0)
    res = M.run_macro_impact("TEST")
    text = " ".join(s["interpretation"] for s in res["sensitivities"]).lower() + res["method"].lower()
    assert not any(w in text for w in CAUSAL_BLOCKLIST)
    assert "bukan kausal" in res["method"]
