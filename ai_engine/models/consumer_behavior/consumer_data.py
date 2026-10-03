import os
import time
import requests
import logging
from typing import Dict, Any, List, Optional
from pytrends.request import TrendReq

logger = logging.getLogger(__name__)

# Basic In-Memory TTL Cache
CACHE = {}
CACHE_TTL = 12 * 3600  # 12 hours

def get_from_cache(key: str) -> Optional[Any]:
    if key in CACHE:
        item, timestamp = CACHE[key]
        if time.time() - timestamp < CACHE_TTL:
            return item
    return None

def set_to_cache(key: str, data: Any):
    CACHE[key] = (data, time.time())

class PyTrendsFetcher:
    def __init__(self):
        # hl='id-ID' for Indonesia, tz=420 is UTC+7
        self.pytrends = TrendReq(hl='id-ID', tz=420)
    
    def fetch_trend(self, keyword: str, timeframe: str = 'today 12-m', geo: str = 'ID') -> Dict[str, Any]:
        cache_key = f"pytrends_{keyword}_{timeframe}_{geo}"
        cached_data = get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
            
        retries = 3
        delay = 2
        
        for attempt in range(retries):
            try:
                self.pytrends.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo, gprop='')
                interest_over_time_df = self.pytrends.interest_over_time()
                
                if interest_over_time_df.empty:
                    result = {"trend_data": [], "mean_interest": 0, "latest_interest": 0}
                else:
                    # Drop isPartial column if exists
                    if 'isPartial' in interest_over_time_df.columns:
                        interest_over_time_df = interest_over_time_df.drop(columns=['isPartial'])
                    
                    mean_val = float(interest_over_time_df[keyword].mean())
                    latest_val = float(interest_over_time_df[keyword].iloc[-1])
                    
                    result = {
                        "trend_data": interest_over_time_df[keyword].tail(12).tolist(), # Last 12 data points
                        "mean_interest": mean_val,
                        "latest_interest": latest_val,
                        "trend_direction": "UP" if latest_val > mean_val else "DOWN"
                    }
                set_to_cache(cache_key, result)
                return result
            except Exception as e:
                logger.warning(f"PyTrends attempt {attempt+1} failed for {keyword}: {e}")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
        
        logger.error(f"Failed to fetch PyTrends data for {keyword} after {retries} attempts.")
        return {"error": "Too Many Requests or PyTrends Error", "trend_data": [], "mean_interest": 0, "latest_interest": 0}


class BPSFetcher:
    def __init__(self):
        self.api_key = os.getenv("BPS_API_KEY", "")
        self.base_url = "https://webapi.bps.go.id/v1/api/list/model/data"
        
        # Semantic Category Mapping (Keyword -> BPS Subject/Variable ID)
        self.mapping = {
            "makanan": {"domain": "0000", "subject": 5}, # Subjek 5: Konsumsi / Pengeluaran
            "minuman": {"domain": "0000", "subject": 5},
            "otomotif": {"domain": "0000", "subject": 8}, # Subjek 8: Transportasi (Example)
            "ritel": {"domain": "0000", "subject": 12}, # Subjek 12: Perdagangan (Example)
            "default": {"domain": "0000", "subject": 5}
        }
        
    def _map_keyword_to_bps(self, keyword: str) -> Dict[str, int]:
        keyword = keyword.lower()
        for key, mapping in self.mapping.items():
            if key in keyword:
                return mapping
        return self.mapping["default"]
        
    def fetch_data(self, keyword: str) -> Dict[str, Any]:
        bps_mapping = self._map_keyword_to_bps(keyword)
        
        cache_key = f"bps_{bps_mapping['domain']}_{bps_mapping['subject']}"
        cached_data = get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
            
        if not self.api_key:
            return {"error": "BPS_API_KEY not configured", "data": []}
            
        url = f"{self.base_url}/domain/{bps_mapping['domain']}/subject/{bps_mapping['subject']}/key/{self.api_key}/"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("data-availability") == "available":
                    result = {"data": data.get("datacontent", {}), "subject": bps_mapping['subject']}
                    set_to_cache(cache_key, result)
                    return result
            return {"error": f"BPS API Error: HTTP {response.status_code}", "data": []}
        except Exception as e:
            logger.error(f"Failed to fetch BPS data: {e}")
            return {"error": str(e), "data": []}

def get_consumer_data(keyword: str, timeframe: str = 'today 12-m') -> Dict[str, Any]:
    pytrends_fetcher = PyTrendsFetcher()
    bps_fetcher = BPSFetcher()
    
    trend_data = pytrends_fetcher.fetch_trend(keyword, timeframe)
    bps_data = bps_fetcher.fetch_data(keyword)
    
    return {
        "keyword": keyword,
        "search_trend": trend_data,
        "macro_indicators": bps_data
    }
