"""Sector intelligence on synthetic prices: no network."""
import numpy as np
import pandas as pd

import ai_engine.models.sector.sector_intelligence as S

CFG = {
    "sectors": {
        "Up": {"label": "Naik", "symbols": ["AAA1", "AAA2", "AAA3"]},
        "Down": {"label": "Turun", "symbols": ["BBB1", "BBB2", "BBB3"]},
        "Flat": {"label": "Datar", "symbols": ["CCC1", "CCC2", "CCC3"]},
    },
    "thresholds": {"rs_bullish": 0.02, "rs_bearish": -0.02, "breadth_bullish": 0.6, "breadth_bearish": 0.4,
                   "min_constituents": 3},
}


def _fake_closes(monkeypatch):
    idx = pd.bdate_range(end="2026-10-08", periods=250)
    n = len(idx)
    data = {"^JKSE": np.full(n, 6000.0)}
    for i in range(1, 4):
        data[f"AAA{i}"] = 1000 * np.exp(np.linspace(0, 0.4, n))     # steady rise
        data[f"BBB{i}"] = 1000 * np.exp(np.linspace(0, -0.4, n))    # steady fall
        data[f"CCC{i}"] = np.full(n, 1000.0)
    monkeypatch.setattr(S, "_closes", lambda symbols: pd.DataFrame(data, index=idx))


def test_sentiment_and_ranking(monkeypatch):
    _fake_closes(monkeypatch)
    out = S.sector_overview(CFG)
    by = {r["sector"]: r for r in out["sectors"]}
    assert by["Up"]["sentiment"] == "Bullish" and by["Up"]["rank"] == 1
    assert by["Down"]["sentiment"] == "Bearish" and by["Down"]["rank"] == 3
    assert by["Flat"]["sentiment"] == "Neutral"
    assert by["Up"]["breadth_ma50"] == 1.0 and by["Down"]["breadth_ma50"] == 0.0
    assert len(by["Up"]["index_weekly"]) > 20


def test_too_few_constituents_are_skipped(monkeypatch):
    _fake_closes(monkeypatch)
    cfg = {**CFG, "sectors": {**CFG["sectors"], "Tiny": {"label": "Kecil", "symbols": ["AAA1"]}}}
    assert "Tiny" not in {r["sector"] for r in S.sector_overview(cfg)["sectors"]}
