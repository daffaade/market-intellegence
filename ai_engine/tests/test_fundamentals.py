from data_processing.data_sectors.fundamentals import map_fundamentals

REPORT = {
    "financials": {
        "historical_financials": [
            {"year": 2024, "revenue": 100e12, "earnings": 50e12},
            {"year": 2023, "revenue": 90e12, "earnings": 40e12},
        ],
        "historical_eps": {"2020": {"eps": 200}, "2023": {"eps": 400}},
    },
    "dividend": {"historical_dividends": {
        "2021": {"total_dividend": 550, "total_yield": 0.018},  # pre-split DPS vs post-split EPS
        "2024": {"total_dividend": 240, "total_yield": 0.025},
    }},
    "ownership": {
        "major_shareholders": [
            {"name": "Public", "share_percentage": "0.45"},
            {"name": "PT Induk", "share_percentage": "0.55"},
        ],
        "top_transactions": {"date": "2026-08-31",
                             "top_buyers": [{"name": "Fund A", "changeAmount": 10}],
                             "top_sellers": [{"name": "Fund B", "changeAmount": -20}]},
        "institutional_transaction_flow": [{"date": "2026-08-31", "net_transaction": -5},
                                           {"date": "2026-07-31", "net_transaction": 3}],
    },
    "management": {"key_executives": [{"name": "Budi", "position": "Direktur"}],
                   "executives_shareholdings": [{"name": "Budi", "share_amount": 1000, "share_percentage": 1e-05}]},
}


def test_map_fundamentals():
    f = map_fundamentals("TEST", REPORT, 0)
    assert [g["year"] for g in f["growth_data"]] == ["2023", "2024"]
    assert f["growth_data"][1] == {"year": "2024", "revenue": 100000.0, "net_profit": 50000.0, "margin": 50.0}
    divs = {d["year"]: d for d in f["dividends"]}
    assert divs["2021"]["payout_ratio"] is None  # 550 / 200 = 275% -> implausible
    assert divs["2024"]["payout_ratio"] == 60.0  # 240 / prior-year EPS 400
    assert f["shareholders"][0] == {"name": "PT Induk", "share_percentage": 55.0, "category": "INSTITUTIONAL"}
    assert f["shareholders"][1]["category"] == "RETAIL"
    assert f["executives"][0]["share_amount"] == 1000
    assert [t["action"] for t in f["smart_money"]] == ["ACCUMULATE", "DISTRIBUTE"]
    assert [p["date"] for p in f["institutional_flow"]] == ["2026-07-31", "2026-08-31"]
