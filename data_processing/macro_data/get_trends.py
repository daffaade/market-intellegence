import time
import logging
from typing import Dict, Any, Optional
try:
    from pytrends.request import TrendReq
except ImportError:
    TrendReq = None

logger = logging.getLogger(__name__)

# Basic In-Memory TTL Cache (Can be replaced with disk cache later)
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
        if TrendReq is not None:
            try:
                # hl='id-ID' for Indonesia, tz=420 is UTC+7
                self.pytrends = TrendReq(hl='id-ID', tz=420)
            except Exception as e:
                logger.warning(f"Failed to initialize TrendReq: {e}")
                self.pytrends = None
        else:
            self.pytrends = None
    
    def fetch_trend(self, keyword: str, timeframe: str = 'today 12-m', geo: str = 'ID') -> Dict[str, Any]:
        cache_key = f"pytrends_{keyword}_{timeframe}_{geo}"
        cached_data = get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
            
        if self.pytrends is None:
            logger.warning(f"PyTrends not available, returning neutral fallback for {keyword}")
            fallback = {
                "trend_data": [50.0] * 12,
                "mean_interest": 50.0,
                "latest_interest": 50.0,
                "trend_direction": "NEUTRAL"
            }
            set_to_cache(cache_key, fallback)
            return fallback

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
