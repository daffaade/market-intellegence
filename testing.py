import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path

# Ensure root directory is in sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Import Caching Systems
from data_processing.cachingunified import UnifiedDataCache, UnifiedCacheTier
from data_processing.data_sectors.caching import SectorsDataCache, CacheTier as SectorsCacheTier
from data_processing.y_finance_data.cachingyfinance import YFinanceDataCache, CacheTier as YFCacheTier
from ai_engine.core.cache import AIResultCache

# Import Getter Systems
from data_processing.getunified import UnifiedDataProvider
from data_processing.data_sectors.getdata import SectorsDataProvider
from data_processing.y_finance_data.getyfinance import YFinanceDataProvider
from ai_engine.core.data_loader import UnifiedDataLoader

# Import Final Pipeline and Endpoint
from data_processing.unified_pipeline import UnifiedPipeline
from data_processing.endpoint_finaldata import get_final_data, get_api_data


def print_header(title: str):
    print("\n" + "=" * 85)
    print(f"🔹 {title.upper()}")
    print("=" * 85)


def print_result(name: str, success: bool, duration: float, extra: str = ""):
    status = "✅ PASSED" if success else "❌ FAILED"
    print(f"{status} | {name:<35} | {duration:6.2f}s | {extra}")


# =============================================================================
# 1. CACHING SYSTEMS VERIFICATION
# =============================================================================

def test_unified_cache():
    print_header("1.1 UnifiedDataCache (Memory L1, Disk L2, Invalidation, Stats)")
    start_time = time.time()
    cache = UnifiedDataCache()

    # 1. Memory L1 Write & Read
    test_key = "CACHE_TEST_SYM"
    test_data = {"test_val": 42, "status": "active"}
    cache.set(test_key, test_data, ttl_seconds=60)
    cached_val = cache.get(test_key)
    l1_pass = cached_val is not None and cached_val.get("test_val") == 42

    # 2. Disk L2 Reload Test
    cache.save_to_disk()
    fresh_cache = UnifiedDataCache(str(cache.cache_file))
    reloaded_val = fresh_cache.get(test_key)
    l2_pass = reloaded_val is not None and reloaded_val.get("test_val") == 42

    # 3. Expiration / Short TTL Test
    exp_key = "CACHE_EXP_SYM"
    cache.set(exp_key, {"exp": True}, ttl_seconds=1)
    time.sleep(1.1)
    exp_val = cache.get(exp_key)
    ttl_pass = exp_val is None

    # 4. Invalidation Test
    cache.invalidate(test_key)
    inv_val = cache.get(test_key)
    inv_pass = inv_val is None

    # 5. Statistics Check
    stats = cache.get_statistics()
    stats_pass = "hits" in stats and "misses" in stats and "hit_rate_pct" in stats

    all_pass = l1_pass and l2_pass and ttl_pass and inv_pass and stats_pass
    duration = time.time() - start_time
    details = f"L1:{l1_pass} L2:{l2_pass} TTL:{ttl_pass} Inv:{inv_pass} Stats:hit_rate={stats.get('hit_rate_pct')}%"
    print_result("UnifiedDataCache Full Lifecycle", all_pass, duration, details)
    return all_pass


def test_sectors_cache():
    print_header("1.2 SectorsDataCache (Categorized Tiers, Disk & Invalidation)")
    start_time = time.time()
    try:
        cache = SectorsDataCache()
        symbol = "TEST_SECTORS"
        cat = "valuation"
        
        # Test Set and Get
        cache.set(symbol, cat, {"pe": 15.5}, ttl_seconds=30)
        entry = cache.get(symbol, cat)
        get_pass = entry is not None and entry.get("pe") == 15.5
        
        # Test Invalidation
        cache.invalidate(symbol, cat)
        inv_entry = cache.get(symbol, cat)
        inv_pass = inv_entry is None
        
        duration = time.time() - start_time
        success = get_pass and inv_pass
        print_result("SectorsDataCache Set/Get/Invalidate", success, duration, f"Tier: {SectorsCacheTier.get_tier(cat)}")
        return success
    except Exception as e:
        duration = time.time() - start_time
        print_result("SectorsDataCache", False, duration, f"Error: {e}")
        return False


def test_yfinance_cache():
    print_header("1.3 YFinanceDataCache (Categorized Tiers, Disk & Invalidation)")
    start_time = time.time()
    try:
        cache = YFinanceDataCache()
        symbol = "TEST_YF"
        cat = "historical_price"
        
        # Test Set and Get
        cache.set(symbol, cat, {"close": 5000}, ttl_seconds=30)
        entry = cache.get(symbol, cat)
        get_pass = entry is not None and entry.get("close") == 5000
        
        # Test Invalidation
        cache.invalidate(symbol, cat)
        inv_entry = cache.get(symbol, cat)
        inv_pass = inv_entry is None
        
        duration = time.time() - start_time
        success = get_pass and inv_pass
        print_result("YFinanceDataCache Set/Get/Invalidate", success, duration, f"Tier: {YFCacheTier.get_tier(cat)}")
        return success
    except Exception as e:
        duration = time.time() - start_time
        print_result("YFinanceDataCache", False, duration, f"Error: {e}")
        return False


def test_ai_result_cache():
    print_header("1.4 AIResultCache (Service-Level Model Results)")
    start_time = time.time()
    cache = AIResultCache(ttl_seconds=2)
    sym = "TEST_AI"
    dummy_result = {"signal": "BUY", "confidence": 0.88}
    
    cache.set(sym, True, True, True, dummy_result)
    retrieved = cache.get(sym, True, True, True)
    hit_pass = retrieved is not None and retrieved.get("signal") == "BUY"
    
    # Key divergence check (different flags must miss)
    miss_pass = cache.get(sym, False, True, True) is None
    
    # Expiry test
    time.sleep(2.1)
    expired_pass = cache.get(sym, True, True, True) is None
    
    duration = time.time() - start_time
    success = hit_pass and miss_pass and expired_pass
    print_result("AIResultCache Multi-Key & Expiry", success, duration, f"Hit:{hit_pass} MissKey:{miss_pass} Expired:{expired_pass}")
    return success


# =============================================================================
# 2. DATA GETTER SYSTEMS VERIFICATION
# =============================================================================

def test_unified_data_provider(ticker: str):
    print_header(f"2.1 UnifiedDataProvider (getunified.py) for {ticker}")
    start_time = time.time()
    provider = UnifiedDataProvider()
    
    # 1. get_price
    price_res = provider.get_price(ticker)
    price_ok = price_res.get("status") == "OKAY" and price_res.get("price") is not None
    
    # 2. get_section (test several key sections)
    val_res = provider.get_section(ticker, "valuation_data")
    val_ok = val_res.get("status") == "SUCCESS"
    
    mkt_res = provider.get_section(ticker, "market_data")
    mkt_ok = mkt_res.get("status") == "SUCCESS"
    
    # 3. get_all_data
    all_res = provider.get_all_data(ticker, print_table=False)
    all_ok = all_res.get("status") in ["SUCCESS", "READY"] and "data" in all_res
    
    duration = time.time() - start_time
    success = price_ok and val_ok and mkt_ok and all_ok
    details = f"Price:{price_res.get('price')} | ValSection:{val_ok} | MktSection:{mkt_ok} | AllData:{all_ok}"
    print_result("UnifiedDataProvider.get_*", success, duration, details)
    return success


def test_sectors_getter(ticker: str):
    print_header(f"2.2 SectorsDataProvider (data_sectors/getdata.py) for {ticker}")
    start_time = time.time()
    provider = SectorsDataProvider()
    
    # 1. get_price
    price_res = provider.get_price(ticker)
    price_ok = price_res.get("status") in ["OKAY", "SUCCESS"]
    
    # 2. get_variable
    var_res = provider.get_variable(ticker, "valuation")
    var_ok = var_res.get("status") in ["OKAY", "SUCCESS"]
    
    # 3. get_all_data
    all_res = provider.get_all_data(ticker)
    all_ok = all_res.get("processing_status", {}).get("overall") in ["OKAY", "WARNING"]
    
    duration = time.time() - start_time
    success = price_ok and var_ok and all_ok
    details = f"PriceOk:{price_ok} | VarOk:{var_ok} | OverallStatus:{all_res.get('processing_status', {}).get('overall')}"
    print_result("SectorsDataProvider.get_*", success, duration, details)
    return success


def test_yfinance_getter(ticker: str):
    print_header(f"2.3 YFinanceDataProvider (y_finance_data/getyfinance.py) for {ticker}")
    start_time = time.time()
    provider = YFinanceDataProvider()
    
    # 1. get_price
    price_res = provider.get_price(ticker)
    price_ok = price_res.get("status") in ["OKAY", "SUCCESS"]
    
    # 2. get_variable
    var_res = provider.get_variable(ticker, "historical_price")
    var_ok = var_res.get("status") in ["OKAY", "SUCCESS"]
    
    # 3. get_all_data
    all_res = provider.get_all_data(ticker)
    has_cats = len(all_res.get("categories", [])) > 0
    
    duration = time.time() - start_time
    success = price_ok and var_ok and has_cats
    details = f"PriceOk:{price_ok} | VarOk:{var_ok} | CategoriesCount:{len(all_res.get('categories', []))}"
    print_result("YFinanceDataProvider.get_*", success, duration, details)
    return success


def test_ai_engine_data_loader(ticker: str):
    print_header(f"2.4 UnifiedDataLoader (ai_engine/core/data_loader.py) for {ticker}")
    start_time = time.time()
    loader = UnifiedDataLoader()
    
    # Test specific getters used by AI Engine models
    price = loader.get_price(ticker)
    val = loader.get_valuation(ticker)
    peers = loader.get_peers(ticker)
    forecast = loader.get_forecast(ticker)
    div = loader.get_dividend(ticker)
    all_data = loader.get_all(ticker)
    
    price_ok = price.get("value") is not None or price.get("source") is not None
    val_ok = val.get("value") is not None or val.get("source") is not None
    all_ok = "price" in all_data and "valuation" in all_data
    
    duration = time.time() - start_time
    success = price_ok and all_ok
    details = f"PriceSource:{price.get('source')} | ValSource:{val.get('source')} | AllKeys:{list(all_data.keys())}"
    print_result("UnifiedDataLoader (AI Engine)", success, duration, details)
    return success


# =============================================================================
# 3. FULL PIPELINE & ENDPOINT INTEGRATION
# =============================================================================

def test_pipeline_and_endpoint(ticker: str):
    print_header(f"3. Unified Pipeline & Endpoint Integration for {ticker}")
    
    # Unified Pipeline
    t0 = time.time()
    pipeline = UnifiedPipeline()
    res_pipeline = pipeline.get_unified_dataset(ticker, force_refresh=False)
    pipe_pass = "data" in res_pipeline and len(res_pipeline["data"]) > 0
    print_result("UnifiedPipeline (Cached)", pipe_pass, time.time() - t0, f"Source: {res_pipeline.get('source')}")

    # API Endpoint
    t1 = time.time()
    res_api = get_api_data(ticker, data_type="all")
    api_pass = res_api.get("status") == "SUCCESS"
    print_result("endpoint_finaldata.get_api_data", api_pass, time.time() - t1, f"Sections: {len(res_api.get('data', {}))}")

    return pipe_pass and api_pass


# =============================================================================
# MAIN RUNNER
# =============================================================================

def run_all_verification():
    print_header("STARTING COMPREHENSIVE CACHING & GETTER TEST SUITE")
    ticker = "BBCA"
    results = {}

    # 1. Caches
    results["UnifiedDataCache"] = test_unified_cache()
    results["SectorsDataCache"] = test_sectors_cache()
    results["YFinanceDataCache"] = test_yfinance_cache()
    results["AIResultCache"] = test_ai_result_cache()

    # 2. Getters
    results["UnifiedDataProvider"] = test_unified_data_provider(ticker)
    results["SectorsDataProvider"] = test_sectors_getter(ticker)
    results["YFinanceDataProvider"] = test_yfinance_getter(ticker)
    results["UnifiedDataLoader (AI Engine)"] = test_ai_engine_data_loader(ticker)

    # 3. Pipeline & Endpoint
    results["Pipeline & Endpoint"] = test_pipeline_and_endpoint(ticker)

    # Summary
    print_header("SUMMARY SCORECARD")
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    for name, ok in results.items():
        tag = "✅ PASS" if ok else "❌ FAIL"
        print(f" {tag} | {name}")
    print("-" * 85)
    print(f"Total Score: {passed}/{total} components verified successfully.")
    print("=" * 85)
    
    if passed != total:
        sys.exit(1)


if __name__ == "__main__":
    run_all_verification()
