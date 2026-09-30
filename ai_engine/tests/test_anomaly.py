import sys
from pathlib import Path
import numpy as np
import math

CURRENT_DIR = Path(__file__).resolve().parent
AI_ENGINE_DIR = CURRENT_DIR.parent
ROOT_DIR = AI_ENGINE_DIR.parent
for p in [str(ROOT_DIR), str(AI_ENGINE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from ai_engine.models.anomaly.isolation_forest import (
    DEFAULT_FEATURE_FIELDS,
    build_feature_matrix,
    impute_missing,
    detect_anomalies_isolation_forest,
    normalize_scores,
    classify_severity,
    build_cross_sectional_dataset,
    detect_market_wide_anomaly,
    combine_time_series_and_cross_sectional,
    compute_adaptive_contamination,
    train_model_with_adaptive_contamination,
    compute_recent_baseline_volatility,
    compute_adaptive_contamination_v2,
    run_training_pipeline_v2,
    cluster_consecutive_anomalies,
    normalize_score_percentile,
    AnomalyModel
)
from ai_engine.core.data_loader import UnifiedDataLoader


def test_isolation_forest_pipeline():
    np.random.seed(42)
    mock_data = []

    tickers = ["BBCA", "BMRI", "BBRI", "BBNI", "TLKM", "ISAT", "EXCL", "ASII", "ICBP", "WEIRD_STOCK"]
    for sym in tickers:
        if sym == "WEIRD_STOCK":
            m = {
                "company": sym,
                "period": "2026-Q1",
                "valuation_metrics": {"pe_relative": 15.5, "pbv_relative": 12.0},
                "growth_metrics": {"revenue_growth_yoy": -85.0, "growth_acceleration": -50.0},
                "price_metrics": {"volatility": 95.0},
                "ownership_metrics": {"net_institutional_flow_pct": -45.0, "insider_ownership_change": -30.0}
            }
        else:
            m = {
                "company": sym,
                "period": "2026-Q1",
                "valuation_metrics": {"pe_relative": 1.0 + np.random.normal(0, 0.1), "pbv_relative": 1.5 + np.random.normal(0, 0.1)},
                "growth_metrics": {"revenue_growth_yoy": 12.0 + np.random.normal(0, 2.0), "growth_acceleration": 1.0 + np.random.normal(0, 0.5)},
                "price_metrics": {"volatility": 18.0 + np.random.normal(0, 2.0)},
                "ownership_metrics": {"net_institutional_flow_pct": 2.0 + np.random.normal(0, 0.5), "insider_ownership_change": 0.0}
            }
        mock_data.append(m)

    # 1. Test Feature Matrix & Imputation
    X_raw, comps = build_feature_matrix(mock_data, DEFAULT_FEATURE_FIELDS)
    assert len(X_raw) == 10
    assert len(comps) == 10
    assert comps[0] == "BBCA"

    X_clean = impute_missing(X_raw, method="median")
    assert X_clean.shape == (10, len(DEFAULT_FEATURE_FIELDS))
    assert not np.isnan(X_clean).any()

    # 2. Test Anomaly Detection
    res = detect_anomalies_isolation_forest(mock_data, contamination=0.10)
    assert res["total_companies_analyzed"] == 10
    assert res["anomalies_detected"] >= 1
    assert "period" in res
    assert len(res["anomalies"]) >= 1

    top_anomaly = res["anomalies"][0]
    assert top_anomaly["company"] == "WEIRD_STOCK"
    assert top_anomaly["anomaly_score"] >= 0.5
    assert top_anomaly["severity"] in ["moderate", "severe"]
    assert len(top_anomaly["contributing_factors"]) > 0

    # 3. Test Normalize Scores
    dummy_scores = [-0.25, -0.10, 0.05, 0.20]
    norm_scores = normalize_scores(dummy_scores)
    assert norm_scores[0] == 1.0
    assert norm_scores[-1] == 0.0

    # 4. Test Classify Severity
    assert classify_severity(0.30) == "normal"
    assert classify_severity(0.60) == "mild"
    assert classify_severity(0.75) == "moderate"
    assert classify_severity(0.90) == "severe"


def test_cross_sectional_and_clusters():
    mock_series = {
        "BBCA": [{"date": f"2025-01-0{i}", "daily_return": 0.5 if i != 3 else -4.5} for i in range(1, 6)],
        "BBRI": [{"date": f"2025-01-0{i}", "daily_return": 0.2 if i != 3 else -4.2} for i in range(1, 6)],
        "BMRI": [{"date": f"2025-01-0{i}", "daily_return": 0.3 if i != 3 else -4.0} for i in range(1, 6)],
    }
    cross_df = build_cross_sectional_dataset(mock_series, ["BBCA", "BBRI", "BMRI"])
    assert len(cross_df) == 5
    assert "BBCA_return" in cross_df[0]

    mw_res = detect_market_wide_anomaly(cross_df, ["BBCA", "BBRI", "BMRI"], threshold_pct=0.6, z_threshold=0.5)
    assert len(mw_res) >= 1

    ts_rows = [{"date": f"2025-01-0{i}", "close": 1000, "is_anomaly": (i == 2), "anomaly_score": 0.8 if i == 2 else 0.2} for i in range(1, 6)]
    combined = combine_time_series_and_cross_sectional(ts_rows, mw_res)
    assert len(combined) == 5
    assert "final_is_anomaly" in combined[0]

    mock_anomaly_points = [
        {"date": "2025-01-02", "score": 0.72, "factors": [{"field": "vol_ratio", "pct": 40.0}]},
        {"date": "2025-01-03", "score": 0.85, "factors": [{"field": "vol_ratio", "pct": 50.0}]},
        {"date": "2025-01-15", "score": 0.65, "factors": [{"field": "intraday_range", "pct": 35.0}]},
    ]
    clusters = cluster_consecutive_anomalies(mock_anomaly_points, max_gap_days=3)
    assert len(clusters) == 2
    assert clusters[0]["n_days"] == 2
    assert clusters[0]["peak_score"] == 0.85


def test_anomaly_model_live():
    loader = UnifiedDataLoader()
    model = AnomalyModel(data_loader=loader)
    res = model.analyze("BBCA")
    assert res.get("status") in ["success", "no_anomalies"]


if __name__ == "__main__":
    test_isolation_forest_pipeline()
    test_cross_sectional_and_clusters()
    test_anomaly_model_live()
    print("All isolation forest tests passed!")
