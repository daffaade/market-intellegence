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

    def _get_key(self, symbol: str, *flags: Any) -> str:
        flags_str = "_".join(str(f) for f in flags)
        return f"{symbol}_{flags_str}"

    def get(self, symbol: str, *flags: Any) -> Optional[Dict[str, Any]]:
        key = self._get_key(symbol, *flags)
        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry["timestamp"] < self.ttl:
                return entry["data"]
            else:
                del self._cache[key]
        return None

    def set(self, symbol: str, *args: Any) -> None:
        if not args:
            return
        *flags, data = args
        key = self._get_key(symbol, *flags)
        self._cache[key] = {
            "timestamp": time.time(),
            "data": data
        }
