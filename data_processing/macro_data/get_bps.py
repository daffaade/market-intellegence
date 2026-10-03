import os
import time
import requests
import logging
from typing import Dict, Any, Optional

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
