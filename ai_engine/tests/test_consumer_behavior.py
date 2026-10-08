"""Consumer behavior: industry resolution and no fabricated data when sources fail."""
import ai_engine.models.consumer_behavior.consumer_behavior_model as C
from ai_engine.models.sector.sector_intelligence import load_sector_map


def test_resolve_sector_by_label_key_and_alias():
    sectors = load_sector_map()["sectors"]
    assert C.resolve_sector("Konsumen primer", sectors) == "Consumer Non-Cyclicals"
    assert C.resolve_sector("Healthcare", sectors) == "Healthcare"
    assert C.resolve_sector("makanan & minuman", sectors) == "Consumer Non-Cyclicals"
    assert C.resolve_sector("antariksa", sectors) is None


def test_unavailable_sources_do_not_invent_data(monkeypatch):
    monkeypatch.setattr(C, "fetch_search_trend", lambda kw: None)
    monkeypatch.setattr(C, "_basket_weekly", lambda syms: (_ for _ in ()).throw(RuntimeError("offline")))
    res = C.ConsumerBehaviorModel().analyze("kopi", "Konsumen primer")
    assert res["search_trend"] is None and res["companies"] == []
    assert "search_trend_unavailable" in res["data_quality_flags"]
    assert res["impact_signal"]["impact_score"] == 50.0
    assert res["impact_signal"]["confidence_level"] == "Low"


def test_unknown_industry_lists_options():
    res = C.ConsumerBehaviorModel().analyze("kopi", "antariksa")
    assert "error" in res and len(res["available_sectors"]) >= 10
