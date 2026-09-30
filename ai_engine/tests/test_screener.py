import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
AI_ENGINE_DIR = CURRENT_DIR.parent
ROOT_DIR = AI_ENGINE_DIR.parent
for p in [str(ROOT_DIR), str(AI_ENGINE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from ai_engine.core.data_loader import UnifiedDataLoader
from ai_engine.models.screener.screener import IntelligenceScreener, ScreenerRequest, ScreenerRule

def test_screener_preset():
    dl = UnifiedDataLoader()
    screener = IntelligenceScreener(dl)
    req = ScreenerRequest(preset="undervalued_growth", tickers=["BBCA", "BMRI", "GOTO"])
    res = screener.screen(req)
    assert res["status"] == "SUCCESS"
    assert "results" in res
    assert "disclaimer" in res

def test_screener_custom_rules():
    dl = UnifiedDataLoader()
    screener = IntelligenceScreener(dl)
    req = ScreenerRequest(
        tickers=["BBCA", "BMRI", "TLKM", "GOTO"],
        rules=[
            ScreenerRule(field="opportunity_score", operator="gte", value=50.0),
            ScreenerRule(field="risk_score", operator="lte", value=50.0)
        ]
    )
    res = screener.screen(req)
    assert res["status"] == "SUCCESS"
    assert res["summary"]["total_scanned"] == 4
    for r in res["results"]:
        assert "rank" in r
        assert "key_findings" in r
        assert "evidence" in r

def test_screener_cache():
    dl = UnifiedDataLoader()
    screener = IntelligenceScreener(dl)
    # Fast re-scan using cached metrics
    req = ScreenerRequest(tickers=["BBCA", "GOTO"])
    res = screener.screen(req)
    assert res["status"] == "SUCCESS"
    assert len(res["results"]) > 0

if __name__ == "__main__":
    test_screener_preset()
    test_screener_custom_rules()
    test_screener_cache()
    print("All screener tests passed!")
