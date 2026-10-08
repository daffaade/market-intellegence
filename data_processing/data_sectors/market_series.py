"""
Daily series from Sectors that the company report does not carry:
net foreign flow per stock and the IHSG index.

Each call costs 1 Sectors credit and returns at most 90 days, so responses are
kept on disk and refetched only when stale:
  - foreign flow: 7 days  (1 credit per symbol per week)
  - IHSG:         1 day   (1 credit per day, shared by every stock)
A per-key lock stops concurrent analyses from paying for the same fetch twice.
"""
import json
import threading
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

CACHE_DIR = Path(__file__).resolve().parent / ".cache" / "series"
FOREIGN_FLOW_TTL = 7 * 24 * 3600
INDEX_TTL = 24 * 3600

_locks: Dict[str, threading.Lock] = {}
_locks_guard = threading.Lock()


def _lock_for(key: str) -> threading.Lock:
    with _locks_guard:
        return _locks.setdefault(key, threading.Lock())


def _cached_fetch(key: str, endpoint: str, ttl: int, miner=None) -> Optional[Dict[str, Any]]:
    """{"fetched_at", "data"} from disk if fresher than ttl, else one Sectors call."""
    path = CACHE_DIR / f"{key}.json"

    def read() -> Optional[Dict[str, Any]]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return payload if time.time() - payload.get("fetched_at", 0) <= ttl else None

    hit = read()
    if hit:
        return hit
    with _lock_for(key):
        hit = read()  # another thread may have fetched while we waited
        if hit:
            return hit
        if miner is None:
            from data_processing.data_sectors.dataminer import SectorsDataMiner
            miner = SectorsDataMiner()
        data = miner._get(endpoint)
        if data is None:
            return None
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        payload = {"fetched_at": time.time(), "data": data}
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload), encoding="utf-8")
        tmp.replace(path)
        return payload


def _window() -> str:
    end = date.today()
    return f"start={(end - timedelta(days=90)).isoformat()}&end={end.isoformat()}"


def get_foreign_flow(symbol: str, miner=None) -> Optional[Dict[str, Any]]:
    """
    Daily net foreign inflow (IDR) for the last 90 days:
    {"fetched_at", "points": [{"date", "net", "buy", "sell", "foreign_share"}...]} oldest first.
    """
    sym = symbol.replace(".JK", "").upper()
    payload = _cached_fetch(f"foreign_flow_{sym}", f"/foreign-flow/{sym}/?{_window()}", FOREIGN_FLOW_TTL, miner)
    if not payload or not isinstance(payload.get("data"), dict):
        return None
    points: List[Dict[str, Any]] = []
    for p in payload["data"].get("data") or []:
        if not p.get("date"):
            continue
        points.append({
            "date": p["date"],
            "net": p.get("net_foreign_inflow"),
            "buy": p.get("foreign_buy_idr"),
            "sell": p.get("foreign_sell_idr"),
            "foreign_share": p.get("foreign_share"),
        })
    points.sort(key=lambda p: p["date"])
    return {"fetched_at": payload["fetched_at"], "points": points}


def get_index_daily(code: str = "ihsg", miner=None) -> Optional[Dict[str, Any]]:
    """Index closes for the last 90 days: {"fetched_at", "points": [{"date", "price"}...]} oldest first."""
    code = code.lower()
    payload = _cached_fetch(f"index_{code}", f"/index-daily/{code}/?{_window()}", INDEX_TTL, miner)
    if not payload or not isinstance(payload.get("data"), list):
        return None
    points = [{"date": p["date"], "price": p.get("price")} for p in payload["data"] if p.get("date") and p.get("price") is not None]
    points.sort(key=lambda p: p["date"])
    return {"fetched_at": payload["fetched_at"], "points": points}
