import os
import sys
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


class UnifiedCacheTier:
    STATIC = "STATIC"       # Company profile, officers, baseline info (7 days)
    PERIODIC = "PERIODIC"   # Valuations, forecasts, ownership, dividends (24 hours)
    FREQUENT = "FREQUENT"   # Market prices, daily volume (1 hour)

    DEFAULT_TTLS = {
        STATIC: 7 * 24 * 3600,
        PERIODIC: 24 * 3600,
        FREQUENT: 3600
    }

    @classmethod
    def get_default_ttl(cls, tier: str) -> int:
        return cls.DEFAULT_TTLS.get(tier, cls.DEFAULT_TTLS[cls.PERIODIC])


class UnifiedCacheEntry:
    def __init__(
        self,
        symbol: str,
        data: Any,
        created_at: Optional[float] = None,
        ttl_seconds: Optional[int] = None,
        discrepancies: Optional[List[dict]] = None
    ):
        self.symbol = symbol.upper()
        self.data = data
        self.created_at = created_at or time.time()
        self.ttl_seconds = ttl_seconds or UnifiedCacheTier.DEFAULT_TTLS[UnifiedCacheTier.PERIODIC]
        self.expires_at = self.created_at + self.ttl_seconds
        self.discrepancies = discrepancies or []

    def is_expired(self, current_time: Optional[float] = None) -> bool:
        now = current_time or time.time()
        return now >= self.expires_at

    @property
    def remaining_ttl(self) -> int:
        return max(0, int(self.expires_at - time.time()))

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "data": self.data,
            "created_at": self.created_at,
            "created_at_iso": datetime.fromtimestamp(self.created_at, tz=timezone.utc).isoformat(),
            "expires_at": self.expires_at,
            "expires_at_iso": datetime.fromtimestamp(self.expires_at, tz=timezone.utc).isoformat(),
            "ttl_seconds": self.ttl_seconds,
            "discrepancies": self.discrepancies
        }

    @classmethod
    def from_dict(cls, d: dict) -> "UnifiedCacheEntry":
        return cls(
            symbol=d["symbol"],
            data=d["data"],
            created_at=d.get("created_at"),
            ttl_seconds=d.get("ttl_seconds"),
            discrepancies=d.get("discrepancies", [])
        )


class UnifiedDataCache:
    """
    Multi-tier Cache Engine for Unified Market Intelligence Data
    with Memory L1 and Disk L2 persistence.
    """

    def __init__(self, cache_file_path: Optional[str] = None):
        if not cache_file_path:
            base_dir = Path(__file__).resolve().parent / ".cache"
            base_dir.mkdir(parents=True, exist_ok=True)
            self.cache_file = base_dir / "unified_cache.json"
        else:
            self.cache_file = Path(cache_file_path)
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)

        self._memory_cache: Dict[str, UnifiedCacheEntry] = {}
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "evictions": 0
        }
        self.load_from_disk()

    def get(self, symbol: str) -> Optional[Dict[str, Any]]:
        sym = symbol.upper().replace(".JK", "")
        entry = self._memory_cache.get(sym)
        if not entry:
            self._stats["misses"] += 1
            return None

        if entry.is_expired():
            del self._memory_cache[sym]
            self._stats["evictions"] += 1
            self._stats["misses"] += 1
            return None

        self._stats["hits"] += 1
        return entry.data

    def set(self, symbol: str, data: Dict[str, Any], ttl_seconds: Optional[int] = None, discrepancies: Optional[List[dict]] = None):
        sym = symbol.upper().replace(".JK", "")
        entry = UnifiedCacheEntry(
            symbol=sym,
            data=data,
            ttl_seconds=ttl_seconds,
            discrepancies=discrepancies
        )
        self._memory_cache[sym] = entry
        self._stats["sets"] += 1
        self.save_to_disk()

    def invalidate(self, symbol: str):
        sym = symbol.upper().replace(".JK", "")
        if sym in self._memory_cache:
            del self._memory_cache[sym]
            self.save_to_disk()

    def clear(self):
        self._memory_cache.clear()
        if self.cache_file.exists():
            try:
                self.cache_file.unlink()
            except Exception:
                pass

    def save_to_disk(self):
        try:
            valid_entries = {
                k: entry.to_dict()
                for k, entry in self._memory_cache.items()
                if not entry.is_expired()
            }
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(valid_entries, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Failed to save unified cache to disk: {e}")

    def load_from_disk(self):
        if not self.cache_file.exists():
            return
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                now = time.time()
                for k, entry_dict in data.items():
                    entry = UnifiedCacheEntry.from_dict(entry_dict)
                    if not entry.is_expired(now):
                        self._memory_cache[k] = entry
        except Exception as e:
            print(f"⚠️ Failed to load unified cache from disk: {e}")

    def get_statistics(self) -> dict:
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total * 100) if total > 0 else 0.0
        return {
            "total_items": len(self._memory_cache),
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate_pct": round(hit_rate, 2),
            "sets": self._stats["sets"],
            "evictions": self._stats["evictions"],
            "cache_file": str(self.cache_file)
        }
