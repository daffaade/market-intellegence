"""Factor scoring on synthetic data: no network, no Sectors credits."""
import numpy as np
import pandas as pd

from ai_engine.models.signal.factor_signal import compute_signals


def _prices(drift: float, vol: float, n: int = 300, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 1000 * np.exp(np.cumsum(drift + vol * rng.standard_normal(n)))
    idx = pd.bdate_range(end="2026-10-08", periods=n)
    return pd.DataFrame({"date": idx, "close": close, "volume": np.full(n, 5e7)})


BENCH = pd.Series(np.linspace(6000, 6100, 300), index=pd.bdate_range(end="2026-10-08", periods=300))
CHEAP_GROWING = {"source": "test", "pe": 6.0, "pe_peer": 10.0, "earnings_growth": 0.25,
                 "inst_net_3m": 2e7, "shares_outstanding": 1e9, "der": 0.3, "sector": "Industrials"}
PRICEY_SHRINKING = {"source": "test", "pe": 30.0, "pe_peer": 10.0, "earnings_growth": -0.30,
                    "inst_net_3m": -2e7, "shares_outstanding": 1e9, "der": 2.4, "sector": "Industrials"}


def run(df, fund, **kw):
    return compute_signals("TEST", df, fundamentals=fund, benchmark=BENCH, **kw)


def test_strong_stock_scores_above_weak_stock():
    strong = run(_prices(0.002, 0.01), CHEAP_GROWING)
    weak = run(_prices(-0.002, 0.03), PRICEY_SHRINKING)
    assert strong["opportunity_signal"]["score"] > 58 > weak["opportunity_signal"]["score"]
    assert strong["opportunity_signal"]["direction"] == "Positive"
    assert weak["risk_signal"]["score"] > strong["risk_signal"]["score"]


def test_forecast_without_skill_has_no_weight():
    base = run(_prices(0.0, 0.01), CHEAP_GROWING, forecast_h7=-0.05, forecast_skill=0.0)
    f = next(x for x in base["factors"] if x["key"] == "forecast")
    assert f["weight"] == 0
    assert base["opportunity_signal"]["score"] == run(_prices(0.0, 0.01), CHEAP_GROWING)["opportunity_signal"]["score"]


def test_missing_fundamentals_lowers_confidence_not_score_validity():
    res = run(_prices(0.0, 0.01), {"source": None})
    keys = {f["key"] for f in res["factors"]}
    assert "valuation" not in keys and "earnings_growth" not in keys
    assert res["opportunity_signal"]["confidence"] != "High"
    assert 1 <= res["opportunity_signal"]["score"] <= 99


def test_meaningless_pe_is_not_used():
    fund = dict(CHEAP_GROWING, pe=18000.0, pe_peer=15.0)
    assert "valuation" not in {f["key"] for f in run(_prices(0.0, 0.01), fund)["factors"]}


def test_divergence_needs_earnings_and_price_to_disagree():
    lagging = _prices(-0.0015, 0.005)  # falls while the benchmark rises
    res = run(lagging, CHEAP_GROWING)
    assert res["fundamental_divergence"]["detected"] and res["fundamental_divergence"]["type"] == "POSITIVE"
    res = run(_prices(0.0, 0.01), {"source": None})
    assert res["fundamental_divergence"]["detected"] is False and res["fundamental_divergence"]["evaluated"] is False


def test_bank_leverage_is_not_penalised():
    fund = dict(CHEAP_GROWING, der=6.0, sector="Financials")
    assert "leverage" not in {f["key"] for f in run(_prices(0.0, 0.01), fund)["factors"]}
