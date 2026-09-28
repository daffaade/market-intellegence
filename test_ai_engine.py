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
from ai_engine.models.smart_money.smart_money_model import SmartMoneyModel
from ai_engine.models.catalyst.catalyst_detector import CatalystDetector
from ai_engine.models.sector.sector_intelligence import SectorIntelligenceModel


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
# 5. SMART MONEY & CATALYST DETECTOR MODELS
# =============================================================================

def test_smart_money_and_catalyst_models(ticker: str = "BBCA"):
    print_header(f"5. Smart Money & Catalyst Detector Models [{ticker}]")
    t0 = time.time()
    
    loader = UnifiedDataLoader()
    
    # 1. Smart Money Model
    sm_model = SmartMoneyModel(data_loader=loader)
    sm_res = sm_model.analyze(ticker)
    sm_ok = (
        sm_res.get("ticker") == ticker and
        "state" in sm_res and
        "score" in sm_res and
        "components" in sm_res
    )
    
    # 2. Catalyst Detector
    cat_model = CatalystDetector(data_loader=loader)
    cat_res = cat_model.analyze(ticker)
    cat_ok = (
        cat_res.get("ticker") == ticker and
        "catalyst_score" in cat_res and
        "net_direction" in cat_res and
        "events" in cat_res
    )
    
    duration = time.time() - t0
    all_ok = sm_ok and cat_ok
    details = (
        f"SM_State:{sm_res.get('state')} | SM_Score:{sm_res.get('score')} | "
        f"Cat_Score:{cat_res.get('catalyst_score')} | Direction:{cat_res.get('net_direction')}"
    )
    print_result("SmartMoney & Catalyst Models", all_ok, duration, details)
    return all_ok


# =============================================================================
# 6. SECTOR INTELLIGENCE MODEL
# =============================================================================

def test_sector_intelligence_model(sector_name: str = "Financials"):
    print_header(f"6. Sector Intelligence Model [{sector_name}]")
    t0 = time.time()
    
    loader = UnifiedDataLoader()
    sec_model = SectorIntelligenceModel(data_loader=loader)
    sec_res = sec_model.analyze_sector(sector_name)
    
    sec_ok = (
        sec_res.get("sector") == sector_name and
        "momentum_score" in sec_res and
        "sentiment_label" in sec_res and
        "metrics" in sec_res
    )
    
    duration = time.time() - t0
    details = (
        f"Sector:{sector_name} | Constituents:{sec_res.get('n_constituents')} | "
        f"Sentiment:{sec_res.get('sentiment_label')} | Momentum:{sec_res.get('momentum_score')}"
    )
    print_result("Sector Intelligence Model", sec_ok, duration, details)
    return sec_ok


# =============================================================================
# 7. FASTAPI REST API INTEGRATION (/api/v1/analyze & /api/v1/sector)
# =============================================================================

def test_fastapi_analyze_endpoint(ticker: str = "BBCA"):
    print_header(f"7. FastAPI REST API (POST /api/v1/analyze & GET /api/v1/sector) [{ticker}]")
    t0 = time.time()
    client = TestClient(app)
    
    # 1. Full Analysis Request
    r1 = client.post("/api/v1/analyze", json={
        "symbol": ticker,
        "include_forecast": True,
        "include_anomaly": True,
        "include_divergence": True,
        "include_smart_money": True,
        "include_catalysts": True
    })
    r1_ok = r1.status_code == 200
    data1 = r1.json() if r1_ok else {}
    has_sections = (
        "forecast" in data1 and
        "fundamental_divergence" in data1 and
        "opportunity_signal" in data1 and
        "anomaly" in data1 and
        "smart_money" in data1 and
        "catalysts" in data1
    )
    c1 = data1.get("cached") is False
    
    # 2. Repeated Request (Must be Cached = True)
    t_cache_start = time.time()
    r2 = client.post("/api/v1/analyze", json={
        "symbol": ticker,
        "include_forecast": True,
        "include_anomaly": True,
        "include_divergence": True,
        "include_smart_money": True,
        "include_catalysts": True
    })
    t_cache_duration = time.time() - t_cache_start
    r2_ok = r2.status_code == 200
    data2 = r2.json() if r2_ok else {}
    c2 = data2.get("cached") is True
    
    # 3. Sector API Endpoint
    r_sec = client.get("/api/v1/sector/Financials")
    sec_api_ok = r_sec.status_code == 200 and r_sec.json().get("sector") == "Financials"
    
    duration = time.time() - t0
    all_ok = r1_ok and has_sections and c1 and r2_ok and c2 and sec_api_ok
    details = (
        f"HTTP:200 | InitialCached:{c1} | RepeatCached:{c2} ({t_cache_duration*1000:.1f}ms) | "
        f"SectorApi:{sec_api_ok}"
    )
    print_result("FastAPI Analyze & Sector APIs", all_ok, duration, details)
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
    
    # 5. Smart Money & Catalyst Models
    results["SmartMoney & Catalyst"] = test_smart_money_and_catalyst_models(ticker)
    
    # 6. Sector Intelligence Model
    results["Sector Intelligence"] = test_sector_intelligence_model("Financials")
    
    # 7. FastAPI Endpoint
    results["FastAPI Analyze & Sector API"] = test_fastapi_analyze_endpoint(ticker)
    
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
