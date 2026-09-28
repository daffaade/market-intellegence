import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
AI_ENGINE_DIR = CURRENT_DIR.parent
ROOT_DIR = AI_ENGINE_DIR.parent
for p in [str(AI_ENGINE_DIR), str(ROOT_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from ai_engine.core.data_loader import UnifiedDataLoader
from ai_engine.models.screener.screener import IntelligenceScreener, ScreenerRequest, ScreenerRule


def test_screener_rule_evaluation():
    loader = UnifiedDataLoader()
    screener = IntelligenceScreener(loader)

    # Test basic operators
    gt_rule = ScreenerRule(field="pe_ratio", operator="gt", value=10)
    assert screener._evaluate_rule(15.5, gt_rule) is True
    assert screener._evaluate_rule(8.0, gt_rule) is False

    lt_rule = ScreenerRule(field="pe_ratio", operator="lt", value=20)
    assert screener._evaluate_rule(15.5, lt_rule) is True
    assert screener._evaluate_rule(25.0, lt_rule) is False

    in_rule = ScreenerRule(field="smart_money_state", operator="in", value=["Accumulation", "Neutral"])
    assert screener._evaluate_rule("Accumulation", in_rule) is True
    assert screener._evaluate_rule("Distribution", in_rule) is False


def test_screener_execution():
    loader = UnifiedDataLoader()
    screener = IntelligenceScreener(loader)

    req = ScreenerRequest(
        universe=["BBCA"],
        logic="AND",
        rules=[
            ScreenerRule(field="opportunity_score", operator="gte", value=0)
        ],
        limit=5
    )

    res = screener.screen(req)
    assert res["status"] == "SUCCESS"
    assert "summary" in res
    assert "results" in res
