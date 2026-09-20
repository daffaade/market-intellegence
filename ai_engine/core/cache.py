import time
from typing import Any, Dict, Optional

class AIResultCache:
    """
    Service-level caching exclusively for AI model outputs.
    Avoid duplicating the data retrieval caching already implemented 
    in data_sectors and y_finance_data.
    """
    def __init__(self, ttl_seconds: int = 3600):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl_seconds

    def _get_key(self, symbol: str, include_forecast: bool, include_anomaly: bool, include_divergence: bool) -> str:
        return f"{symbol}_{include_forecast}_{include_anomaly}_{include_divergence}"

    def get(self, symbol: str, include_forecast: bool, include_anomaly: bool, include_divergence: bool) -> Optional[Dict[str, Any]]:
        key = self._get_key(symbol, include_forecast, include_anomaly, include_divergence)
        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry["timestamp"] < self.ttl:
                return entry["data"]
            else:
                del self._cache[key]
        return None

    def set(self, symbol: str, include_forecast: bool, include_anomaly: bool, include_divergence: bool, data: Dict[str, Any]) -> None:
        key = self._get_key(symbol, include_forecast, include_anomaly, include_divergence)
        self._cache[key] = {
            "timestamp": time.time(),
            "data": data
        }
