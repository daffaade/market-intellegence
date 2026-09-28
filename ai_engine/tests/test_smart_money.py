
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
AI_ENGINE_DIR = CURRENT_DIR.parent
if str(AI_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_ENGINE_DIR))

from models.smart_money.smart_money_model import SmartMoneyModel

def test_smart_money_normal():
    model = SmartMoneyModel()
    res = model.analyze("BBCA")
    assert res["ticker"] == "BBCA"
    assert "score" in res
    assert "state" in res
    assert isinstance(res["evidence"], list)

def test_smart_money_anti_look_ahead():
    model = SmartMoneyModel()
    res = model.analyze("BBCA", as_of="2023-01-01")
    assert res["ticker"] == "BBCA"
    assert "score" in res

def test_smart_money_empty():
    model = SmartMoneyModel()
    res = model.analyze("INVALIDTICKER")
    assert "empty_price_data" in res["data_quality_flags"]
    assert res["confidence"] == "low"
