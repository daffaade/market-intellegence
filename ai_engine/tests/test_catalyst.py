
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
AI_ENGINE_DIR = CURRENT_DIR.parent
if str(AI_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_ENGINE_DIR))

from models.catalyst.catalyst_detector import CatalystDetector

def test_catalyst_normal():
    model = CatalystDetector()
    res = model.analyze("BBCA")
    assert res["ticker"] == "BBCA"
    assert "catalyst_score" in res
    assert "net_direction" in res
    assert isinstance(res["events"], list)

def test_catalyst_anti_look_ahead():
    model = CatalystDetector()
    res = model.analyze("BBCA", as_of="2023-01-01")
    assert res["ticker"] == "BBCA"
    assert "catalyst_score" in res

def test_catalyst_empty():
    model = CatalystDetector()
    res = model.analyze("INVALIDTICKER")
    assert "empty_price_data" in res["data_quality_flags"]
    assert res["net_direction"] == "None"
