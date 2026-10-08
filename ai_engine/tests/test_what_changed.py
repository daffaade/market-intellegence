from ai_engine.models.peers.what_changed import changes_from_report

REPORT = {
    "overview": {"sector": "Industrials"},
    "financials": {
        "historical_financials": [
            {"year": 2024, "revenue": 100e12, "earnings": 10e12},
            {"year": 2025, "revenue": 130e12, "earnings": 9.5e12},
        ],
        "historical_financial_ratio": [
            {"year": "2024", "profitability": {"roe": 0.10, "net_profit_margin": 0.10}, "leverage": {"debt_to_equity_ratio": 1.0}},
            {"year": "2025", "profitability": {"roe": 0.13, "net_profit_margin": 0.073}, "leverage": {"debt_to_equity_ratio": 1.5}},
        ],
    },
    "valuation": {"historical_valuation": [{"year": 2025, "pe": -50.0}, {"year": 2026, "pe": 12.0}]},
}


def test_year_over_year_changes_and_direction():
    changes = {c["metric"]: c for c in changes_from_report(REPORT)}
    assert changes["Pendapatan"]["favorable"] is True and changes["Pendapatan"]["period"] == "2024→2025"
    assert "Laba bersih" not in changes  # -5% is below the 10% threshold
    assert changes["ROE"]["delta_text"] == "+3,0 poin" and changes["ROE"]["favorable"] is True
    assert changes["Marjin laba bersih"]["favorable"] is False
    assert changes["Utang terhadap ekuitas"]["favorable"] is False
    assert "PER" not in changes  # negative PER is not a valuation


def test_bank_leverage_is_skipped():
    bank = dict(REPORT, overview={"sector": "Financials"})
    assert "Utang terhadap ekuitas" not in {c["metric"] for c in changes_from_report(bank)}
