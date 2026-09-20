import sys
import time
import json
from pathlib import Path

# Add root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from ai_engine.main import app
from ai_engine.core.data_loader import UnifiedDataLoader
from ai_engine.core.cache import AIResultCache
from ai_engine.models.forecast.forecast_model import ForecastModel
from ai_engine.models.anomaly.isolation_forest import AnomalyModel
from ai_engine.models.peers.peer_analysis import PeerAnalysisModel
from ai_engine.models.peers.what_changed import WhatChangedModel


def print_header(title: str):
    print("\n" + "=" * 85)
    print(f"🤖 {title.upper()}")
    print("=" * 85)


def print_result(name: str, success: bool, duration: float, extra: str = ""):
    status = "✅ PASSED" if success else "❌ FAILED"
    print(f"{status} | {name:<35} | {duration:6.2f}s | {extra}")


# =============================================================================
# 1. DATA SYNCHRONIZATION WITH DATA_PROCESSING
# =============================================================================

def test_data_loader_synchronization(ticker: str = "BBCA"):
    print_header(f"1. Data Loader Synchronization (Data Processing -> AI Engine) [{ticker}]")
    t0 = time.time()
    
    loader = UnifiedDataLoader()
    
    # 1. Check provider initialization
    prov_ok = (
        loader.sectors_provider is not None and
        loader.yfinance_provider is not None and
        loader.unified_provider is not None
    )
    
    # 2. Variable routing (Short-term -> sectors, Long-term -> yfinance)
    p_short = loader.get_price(ticker, period="current")
    p_long = loader.get_price(ticker, period="10y")
    route_ok = p_short.get("source") == "sectors" and p_long.get("source") == "yfinance"
    
    # 3. Direct Unified Dataset access through DataLoader
    unified_ds = loader.get_unified_dataset(ticker)
    has_unified = "data" in unified_ds and len(unified_ds["data"]) > 0
    
    # 4. Section access through DataLoader
    val_sec = loader.get_section(ticker, "valuation_data")
    sec_ok = val_sec.get("status") == "SUCCESS" and "data" in val_sec
    
    duration = time.time() - t0
    all_ok = prov_ok and route_ok and has_unified and sec_ok
    details = f"Providers:{prov_ok} | Routing:{route_ok} | UnifiedDS:{has_unified} | Section:{sec_ok}"
    print_result("DataLoader Synchronization", all_ok, duration, details)
    return all_ok


# =============================================================================
# 2. FORECAST MODEL VERIFICATION
# =============================================================================

def test_forecast_model(ticker: str = "BBCA"):
    print_header(f"2. ForecastModel (Multi-Horizon RF + Signal Engine) [{ticker}]")
    t0 = time.time()
    
    loader = UnifiedDataLoader()
    model = ForecastModel(data_loader=loader)
    
    res = model.analyze(ticker)
    status_ok = res.get("status") == "success"
    
    # Verify forecast structure
    fc = res.get("forecast", {})
    curve = fc.get("horizon_curve", {})
    has_horizons = all(f"H+{h}" in curve for h in [1, 2, 3, 4, 5, 6, 7])
    
    # Verify signals
    opp = res.get("opportunity_signal", {})
    risk = res.get("risk_signal", {})
    has_scores = "score" in opp and "score" in risk
    
    duration = time.time() - t0
    all_ok = status_ok and has_horizons and has_scores
    details = (
        f"Status:{res.get('status')} | Horizons:{len(curve)}/7 | "
        f"OppScore:{opp.get('score')} | RiskScore:{risk.get('score')}"
    )
    print_result("ForecastModel Multi-Horizon", all_ok, duration, details)
    return all_ok


# =============================================================================
# 3. ANOMALY DETECTION MODEL VERIFICATION
# =============================================================================

def test_anomaly_model(ticker: str = "BBCA"):
    print_header(f"3. AnomalyModel (Isolation Forest + False Positive Filter) [{ticker}]")
    t0 = time.time()
    
    loader = UnifiedDataLoader()
    model = AnomalyModel(data_loader=loader)
    
    res = model.analyze(ticker)
    status_ok = res.get("status") == "success"
    
    # Check fields
    episodes = res.get("episodes", [])
    n_anomalies = res.get("detected_anomalies_count", 0)
    baseline_vol = res.get("recent_baseline_volatility")
    
    duration = time.time() - t0
    all_ok = status_ok and n_anomalies >= 0 and baseline_vol is not None
    details = (
        f"Status:{res.get('status')} | AnomaliesFound:{n_anomalies} | "
        f"Episodes:{len(episodes)} | BaselineVol:{baseline_vol:.4f}"
    )
    print_result("AnomalyModel IsolationForest", all_ok, duration, details)
    return all_ok


# =============================================================================
# 4. PEER ANALYSIS & WHAT CHANGED MODELS
# =============================================================================

def test_peer_and_what_changed_models(ticker: str = "BBCA"):
    print_header(f"4. Peer Analysis & What Changed Models [{ticker}]")
    t0 = time.time()
    
    loader = UnifiedDataLoader()
    
    # Peer Analysis Model
    peer_model = PeerAnalysisModel(data_loader=loader)
    peer_res = peer_model.analyze(ticker)
    peer_ok = (
        peer_res.get("status") == "success" and
        "relative_positions" in peer_res and
        "divergence_score" in peer_res
    )
    
    # What Changed Model
    what_model = WhatChangedModel(data_loader=loader)
    what_res = what_model.analyze(ticker)
    what_ok = (
        what_res.get("status") == "success" and
        "significant_changes" in what_res
    )
    
    duration = time.time() - t0
    all_ok = peer_ok and what_ok
    details = (
        f"PeerGroup:{len(peer_res.get('peer_group', []))} | "
        f"DivergenceScore:{peer_res.get('divergence_score')} | "
        f"ShiftsDetected:{what_res.get('total_changes')}"
    )
    print_result("Peer & WhatChanged Models", all_ok, duration, details)
    return all_ok


# =============================================================================
# 5. FASTAPI REST API INTEGRATION (/api/v1/analyze)
# =============================================================================

def test_fastapi_analyze_endpoint(ticker: str = "BBCA"):
    print_header(f"5. FastAPI REST API (POST /api/v1/analyze) [{ticker}]")
    t0 = time.time()
    client = TestClient(app)
    
    # 1. Full Analysis Request
    r1 = client.post("/api/v1/analyze", json={
        "symbol": ticker,
        "include_forecast": True,
        "include_anomaly": True,
        "include_divergence": True
    })
    r1_ok = r1.status_code == 200
    data1 = r1.json() if r1_ok else {}
    has_sections = (
        "forecast" in data1 and
        "fundamental_divergence" in data1 and
        "opportunity_signal" in data1 and
        "anomaly" in data1
    )
    c1 = data1.get("cached") is False
    
    # 2. Repeated Request (Must be Cached = True)
    t_cache_start = time.time()
    r2 = client.post("/api/v1/analyze", json={
        "symbol": ticker,
        "include_forecast": True,
        "include_anomaly": True,
        "include_divergence": True
    })
    t_cache_duration = time.time() - t_cache_start
    r2_ok = r2.status_code == 200
    data2 = r2.json() if r2_ok else {}
    c2 = data2.get("cached") is True
    
    # 3. Selective Request (Only Forecast)
    r3 = client.post("/api/v1/analyze", json={
        "symbol": ticker,
        "include_forecast": True,
        "include_anomaly": False,
        "include_divergence": False
    })
    r3_ok = r3.status_code == 200
    data3 = r3.json() if r3_ok else {}
    selective_ok = data3.get("forecast") is not None and data3.get("anomaly") is None
    
    duration = time.time() - t0
    all_ok = r1_ok and has_sections and c1 and r2_ok and c2 and r3_ok and selective_ok
    details = (
        f"HTTP:200 | InitialCached:{c1} | RepeatCached:{c2} ({t_cache_duration*1000:.1f}ms) | "
        f"SelectiveFlagsOk:{selective_ok}"
    )
    print_result("FastAPI /api/v1/analyze", all_ok, duration, details)
    return all_ok


# =============================================================================
# MAIN RUNNER
# =============================================================================

def run_all_tests():
    print_header("STARTING AI_ENGINE & DATA_PROCESSING INTEGRATION TEST SUITE")
    ticker = "BBCA"
    results = {}
    
    # 1. Synchronization
    results["DataLoader Sync"] = test_data_loader_synchronization(ticker)
    
    # 2. Forecast Model
    results["Forecast Model"] = test_forecast_model(ticker)
    
    # 3. Anomaly Model
    results["Anomaly Model"] = test_anomaly_model(ticker)
    
    # 4. Peer & What Changed
    results["Peer & What Changed"] = test_peer_and_what_changed_models(ticker)
    
    # 5. FastAPI Endpoint
    results["FastAPI Analyze API"] = test_fastapi_analyze_endpoint(ticker)
    
    # Scorecard
    print_header("AI_ENGINE VERIFICATION SCORECARD")
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    for name, ok in results.items():
        tag = "✅ PASS" if ok else "❌ FAIL"
        print(f" {tag} | {name}")
    print("-" * 85)
    print(f"Total Score: {passed}/{total} AI Engine components verified successfully.")
    print("=" * 85)
    
    if passed != total:
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
