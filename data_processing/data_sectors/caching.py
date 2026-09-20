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

# Setup sys.path
_SUB_DIR = Path(__file__).resolve().parent
_PKG_DIR = _SUB_DIR.parent
_ROOT_DIR = _PKG_DIR.parent
for _p in [str(_ROOT_DIR), str(_PKG_DIR), str(_SUB_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from data_processing.data_sectors.dataminer import SectorsDataMiner, SectorsDataValidator
from data_processing.data_sectors.datanormalise import SectorsDataNormalizer


# =====================================================================
# CACHE TIERS & SPECIFICATIONS
# =====================================================================

class CacheTier:
    """
    Tier classification based on data volatility from cachingdata.md:
    1. STATIC: Slow changing (Company profile, Executives, Major shareholders) -> 7 days
    2. PERIODIC: Periodic updates (Financials, Valuation, Institutional tx, Dividend) -> 24 hours
    3. FREQUENT: Fast changing (Stock price, Volume, Market data, Daily prices) -> 15 minutes / 1 hour
    """
    STATIC = "STATIC"
    PERIODIC = "PERIODIC"
    FREQUENT = "FREQUENT"

    # Default TTLs in seconds
    DEFAULT_TTLS = {
        STATIC: 7 * 24 * 3600,     # 7 days (604,800s)
        PERIODIC: 24 * 3600,       # 24 hours (86,400s)
        FREQUENT: 3600             # 1 hour (3,600s) for daily EOD / market price
    }

    # Category routing map
    CATEGORY_TIERS = {
        # Static / Slow Changing
        "company_profile": STATIC,
        "executives": STATIC,
        "key_executives": STATIC,
        "major_shareholders": STATIC,
        "executive_shareholdings": STATIC,
        "shareholder_composition": STATIC,

        # Periodic Data
        "valuation": PERIODIC,
        "peer": PERIODIC,
        "future_forecast": PERIODIC,
        "financial_data": PERIODIC,
        "dividend": PERIODIC,
        "institutional_transactions": PERIODIC,

        # Frequently Changing Data (Daily EOD Prices)
        "historical_price": PERIODIC,
        "stock_price": FREQUENT,
        "volume": FREQUENT,
        "market_data": FREQUENT,
        "daily_prices": PERIODIC
    }

    @classmethod
    def get_tier(cls, category: str) -> str:
        cat_clean = category.lower().replace(" ", "_")
        return cls.CATEGORY_TIERS.get(cat_clean, cls.PERIODIC)

    @classmethod
    def get_default_ttl(cls, tier: str) -> int:
        return cls.DEFAULT_TTLS.get(tier, cls.DEFAULT_TTLS[cls.PERIODIC])


class CacheEntry:
    """Represents an individual cached item with metadata and expiration tracking."""
    def __init__(
        self,
        symbol: str,
        category: str,
        tier: str,
        data: Any,
        created_at: Optional[float] = None,
        ttl_seconds: Optional[int] = None
    ):
        self.symbol = symbol.upper()
        self.category = category.lower()
        self.tier = tier
        self.data = data
        self.created_at = created_at or time.time()
        self.ttl_seconds = ttl_seconds or CacheTier.get_default_ttl(tier)
        self.expires_at = self.created_at + self.ttl_seconds

    def is_expired(self, current_time: Optional[float] = None) -> bool:
        now = current_time or time.time()
        return now >= self.expires_at

    @property
    def remaining_ttl(self) -> int:
        remaining = int(self.expires_at - time.time())
        return max(0, remaining)

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "category": self.category,
            "tier": self.tier,
            "data": self.data,
            "created_at": self.created_at,
            "created_at_iso": datetime.fromtimestamp(self.created_at, tz=timezone.utc).isoformat(),
            "expires_at": self.expires_at,
            "expires_at_iso": datetime.fromtimestamp(self.expires_at, tz=timezone.utc).isoformat(),
            "ttl_seconds": self.ttl_seconds
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CacheEntry":
        return cls(
            symbol=d["symbol"],
            category=d["category"],
            tier=d.get("tier", CacheTier.PERIODIC),
            data=d["data"],
            created_at=d.get("created_at"),
            ttl_seconds=d.get("ttl_seconds")
        )


# =====================================================================
# DATA CACHE MODULE (L1 Memory + L2 Persistent Storage)
# =====================================================================

class SectorsDataCache:
    """
    Multi-tier Caching Engine with in-memory (L1) and persistent file (L2) storage.
    Supports auto-tiering, TTL invalidation, statistics, and local disk persistence.
    """

    def __init__(self, cache_file_path: Optional[str] = None):
        if not cache_file_path:
            base_dir = Path(__file__).resolve().parent / ".cache"
            base_dir.mkdir(parents=True, exist_ok=True)
            self.cache_file = base_dir / "sectors_cache.json"
        else:
            self.cache_file = Path(cache_file_path)
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)

        self._memory_cache: Dict[str, CacheEntry] = {}
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "evictions": 0
        }
        self.load_from_disk()

    def _make_key(self, symbol: str, category: str) -> str:
        return f"{symbol.upper()}:{category.lower()}"

    def get(self, symbol: str, category: str) -> Optional[Any]:
        """Retrieves cached item if present and not expired."""
        key = self._make_key(symbol, category)
        entry = self._memory_cache.get(key)

        if not entry:
            self._stats["misses"] += 1
            return None

        if entry.is_expired():
            # Invalidate expired entry
            del self._memory_cache[key]
            self._stats["evictions"] += 1
            self._stats["misses"] += 1
            return None

        self._stats["hits"] += 1
        return entry.data

    def get_entry(self, symbol: str, category: str) -> Optional[CacheEntry]:
        """Retrieves full CacheEntry metadata object if present and not expired."""
        key = self._make_key(symbol, category)
        entry = self._memory_cache.get(key)
        if not entry or entry.is_expired():
            return None
        return entry

    def set(
        self,
        symbol: str,
        category: str,
        data: Any,
        tier: Optional[str] = None,
        ttl_seconds: Optional[int] = None
    ) -> CacheEntry:
        """Stores data into cache with auto-tiering or custom TTL."""
        std_tier = tier or CacheTier.get_tier(category)
        entry = CacheEntry(
            symbol=symbol,
            category=category,
            tier=std_tier,
            data=data,
            ttl_seconds=ttl_seconds
        )
        key = self._make_key(symbol, category)
        self._memory_cache[key] = entry
        self._stats["sets"] += 1
        return entry

    def set_dataset(self, symbol: str, normalized_dataset: Dict[str, Any]):
        """Caches an entire normalized dataset across appropriate tiers."""
        for category, content in normalized_dataset.items():
            self.set(symbol, category, content)
        self.save_to_disk()

    def get_all_for_symbol(self, symbol: str) -> Dict[str, Any]:
        """Returns all currently valid cached categories for a symbol."""
        prefix = f"{symbol.upper()}:"
        result = {}
        for key, entry in list(self._memory_cache.items()):
            if key.startswith(prefix):
                if not entry.is_expired():
                    result[entry.category] = entry.data
                else:
                    del self._memory_cache[key]
                    self._stats["evictions"] += 1
        
        if result:
            self._stats["hits"] += len(result)
        else:
            self._stats["misses"] += 1
            
        return result

    def invalidate(self, symbol: Optional[str] = None, category: Optional[str] = None):
        """Invalidates specific symbol/category cache or all entries for a symbol."""
        if symbol and category:
            key = self._make_key(symbol, category)
            if key in self._memory_cache:
                del self._memory_cache[key]
        elif symbol:
            prefix = f"{symbol.upper()}:"
            keys_to_del = [k for k in self._memory_cache if k.startswith(prefix)]
            for k in keys_to_del:
                del self._memory_cache[k]
        self.save_to_disk()

    def clear(self):
        """Clears entire cache memory and disk."""
        self._memory_cache.clear()
        if self.cache_file.exists():
            try:
                self.cache_file.unlink()
            except Exception:
                pass

    def save_to_disk(self):
        """Persists memory cache to disk file."""
        try:
            # Filter out expired items before saving
            valid_entries = {
                k: entry.to_dict()
                for k, entry in self._memory_cache.items()
                if not entry.is_expired()
            }
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(valid_entries, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Failed to persist cache to disk: {e}")

    def load_from_disk(self):
        """Loads cached items from disk file into memory."""
        if not self.cache_file.exists():
            return
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                now = time.time()
                for k, entry_dict in data.items():
                    entry = CacheEntry.from_dict(entry_dict)
                    if not entry.is_expired(now):
                        self._memory_cache[k] = entry
        except Exception as e:
            print(f"⚠️ Failed to load cache from disk: {e}")

    def get_statistics(self) -> dict:
        """Returns cache telemetry and statistics."""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total_requests) if total_requests > 0 else 0.0

        # Group count by tier
        tier_counts = {CacheTier.STATIC: 0, CacheTier.PERIODIC: 0, CacheTier.FREQUENT: 0}
        for entry in self._memory_cache.values():
            if not entry.is_expired():
                tier_counts[entry.tier] = tier_counts.get(entry.tier, 0) + 1

        return {
            "total_items": len(self._memory_cache),
            "tier_breakdown": tier_counts,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate_pct": round(hit_rate * 100, 2),
            "sets": self._stats["sets"],
            "evictions": self._stats["evictions"],
            "cache_file": str(self.cache_file)
        }


# =====================================================================
# UNIFIED PIPELINE (Miner -> Validator -> Normalizer -> Cache -> Engine)
# =====================================================================

class SectorsPipeline:
    """
    Coordinates data flow from API extraction through Validation, Normalization,
    and Tiered Caching, delivering ready datasets for the Intelligence Engine.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.miner = SectorsDataMiner(api_key=api_key)
        self.validator = SectorsDataValidator()
        self.normalizer = SectorsDataNormalizer()
        self.cache = SectorsDataCache()

    def get_dataset(self, symbol: str = "BBCA", force_refresh: bool = False) -> Dict[str, Any]:
        """
        Executes full data pipeline:
        1. Checks cache for symbol categories
        2. If missing or forced:
           - Mines raw data
           - Validates schema and integrity
           - Normalizes fields and formats
           - Stores normalized categories into tiered cache
        3. Returns standardized payload for Intelligence Engine.
        """
        clean_symbol = symbol.replace(".JK", "").upper()
        
        # Check cache if not forcing refresh
        if not force_refresh:
            cached_data = self.cache.get_all_for_symbol(clean_symbol)
            # Ensure critical categories are present in cache
            if cached_data and len(cached_data) >= 7 and "historical_price" in cached_data:
                return {
                    "source": "CACHE_HIT",
                    "symbol": clean_symbol,
                    "status": "READY",
                    "data": cached_data,
                    "validation": {"status": "VALID", "message": "Pre-validated in cache"},
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

        # Step 1: Data Mining
        raw_mined_data, validation_report = self.miner.mine_sample_data(clean_symbol, validate=True)

        # Step 2: Data Validation
        if not validation_report:
            validation_report = self.validator.validate_mined_dataset(raw_mined_data)

        # Step 3: Data Normalization
        normalized_data, norm_meta = self.normalizer.normalize_dataset(raw_mined_data)

        # Step 4: Tiered Data Caching
        self.cache.set_dataset(clean_symbol, normalized_data)

        # Step 5: Package for Intelligence Engine
        return {
            "source": "API_MINED_AND_NORMALIZED",
            "symbol": clean_symbol,
            "status": "READY" if validation_report.get("is_valid") else "VALIDATION_WARNING",
            "validation": validation_report,
            "normalization": norm_meta,
            "data": normalized_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


def display_caching_and_pipeline(symbol: str, pipeline_result: dict, cache_stats: dict):
    """Prints comprehensive pipeline & caching status report."""
    print("=" * 75)
    print(f"🚀 SECTORS INTELLIGENCE PIPELINE RESULT: {symbol.upper()}")
    print("=" * 75)
    
    print(f"\n📡 Pipeline Source : {pipeline_result['source']}")
    print(f"🛡️  Engine Status   : {pipeline_result['status']}")
    print(f"⏰ Timestamp       : {pipeline_result['timestamp']}")

    print("\n" + "-" * 75)
    print("🗂️  CACHED DATA TIERS BREAKDOWN")
    print("-" * 75)
    
    data = pipeline_result.get("data", {})
    for category, content in data.items():
        tier = CacheTier.get_tier(category)
        ttl = CacheTier.get_default_ttl(tier)
        tier_icon = "🟢 [STATIC]" if tier == CacheTier.STATIC else ("🟡 [PERIODIC]" if tier == CacheTier.PERIODIC else "🔴 [FREQUENT]")
        print(f"\n{tier_icon} {category.upper()} (TTL: {ttl}s)")
        print(json.dumps(content, indent=2, ensure_ascii=False))

    print("\n" + "=" * 75)
    print("📊 CACHE TELEMETRY & STATS")
    print("=" * 75)
    print(f"📦 Total Cached Items : {cache_stats['total_items']}")
    print(f"🎯 Cache Hits / Misses: {cache_stats['hits']} Hits / {cache_stats['misses']} Misses")
    print(f"⚡ Hit Rate           : {cache_stats['hit_rate_pct']}%")
    print(f"🗄️  Tier Distribution : Static: {cache_stats['tier_breakdown'].get('STATIC', 0)} | Periodic: {cache_stats['tier_breakdown'].get('PERIODIC', 0)} | Frequent: {cache_stats['tier_breakdown'].get('FREQUENT', 0)}")
    print(f"💾 Storage File       : {cache_stats['cache_file']}")
    print("=" * 75)


if __name__ == "__main__":
    target_symbol = sys.argv[1] if len(sys.argv) > 1 else "BBCA"
    
    pipeline = SectorsPipeline()
    print(f"▶️ [RUN 1] Requesting data for {target_symbol} (Expected: API Mining & Cache Population)...")
    res1 = pipeline.get_dataset(target_symbol)
    
    print(f"\n▶️ [RUN 2] Requesting data again for {target_symbol} (Expected: Cache Hit)...")
    res2 = pipeline.get_dataset(target_symbol)

    stats = pipeline.cache.get_statistics()
    display_caching_and_pipeline(target_symbol, res2, stats)
