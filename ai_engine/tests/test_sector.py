
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
AI_ENGINE_DIR = CURRENT_DIR.parent
if str(AI_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_ENGINE_DIR))

from models.sector.sector_intelligence import SectorIntelligenceModel

def test_sector_normal():
    model = SectorIntelligenceModel()
    res = model.analyze_sector("Financials")
    assert res["sector"] == "Financials"
    assert "momentum_score" in res
    assert "sentiment_label" in res
    assert isinstance(res["evidence"], list)

def test_sector_anti_look_ahead():
    model = SectorIntelligenceModel()
    res = model.analyze_sector("Financials", as_of="2023-01-01")
    assert res["sector"] == "Financials"
    assert "momentum_score" in res

def test_sector_invalid():
    model = SectorIntelligenceModel()
    res = model.analyze_sector("INVALIDSECTOR")
    assert res["low_confidence"] == True
    assert "Insufficient constituents" in res["evidence"]
