---
name: sectors-quota-guard
description: Use when adding or changing any code that fetches data from the Sectors API (api.sectors.app), or any code path that could trigger an external data fetch, to protect the team's hard limit of 1,000 Sectors API credits through the three-layer cache
---

# Sectors Quota Guard (1,000 Credits)

## Overview
The Sectors API gives the team 1,000 credits in total. Every extra call costs quota the team cannot get back. The platform protects that quota with three cache layers. Any new code that reaches Sectors must go through the cache, and a repeat request for the same ticker must never call the API again.

Source of truth: `AGENTS.md` section 3, Constraint 2.

| Layer | Location | TTL |
|---|---|---|
| 1. Raw file cache | `data_processing/data_sectors/caching.py`, `getdata.py`, `cachingunified.py` | Persistent file cache |
| 2. Engine memory cache | `ai_engine/core/cache.py` (`ttl_seconds=3600`) | 1 hour |
| 3. Backend snapshot cache | `backend` (`CACHE_TTL_HOURS=24`) | 24 hours |

Repeated requests for the same ticker must return in under 5 ms with zero external calls.

## When to Use
- Writing a new function that calls `https://api.sectors.app` or uses `SECTORS_API_KEY`.
- Adding a new endpoint or job that loops over the universe (`BBCA`, `BBRI`, `BMRI`, `BBNI`, `TLKM`, `ASII`, `AMRT`, `GOTO`, `ANTM`, `BUMI`) or over sectors.
- Changing a TTL, a cache key, or the refresh logic.
- Running a backfill or pipeline script that could fetch the whole universe.

## Procedure

1. **Find every outbound Sectors call.** Use this to confirm that nothing bypasses the cache:
   ```bash
   cd ~/market-intellegence
   grep -rn "sectors.app\|SECTORS_API_KEY\|SECTORS_BASE_URL" --include=*.py --include=*.go . | grep -v __pycache__
   ```
   Expected: calls only inside `data_processing/data_sectors/` (the miner is in `dataminer.py`). Anything else is a violation.

2. **Route new fetches through the existing cache.** Read `data_processing/data_sectors/getdata.py` first and reuse its entry point. Do not write a second HTTP client. The check order must be cache first, network second, and the network path must write back to the cache.

3. **Keep `MOCK_SECTORS` working.** The backend reads `MOCK_SECTORS` (`backend/internal/platform/config/config.go`). Tests and local work must run with `MOCK_SECTORS=true` and make zero credit calls.

4. **Verify with zero spend.** Run the tests with mock mode on, and check that the cache hit path makes no network call. Count calls with a stub or a patched client, not with the live key.

5. **Note the base URL discrepancy.** `data_processing/data_sectors/dataminer.py` uses `https://api.sectors.app/v2`, while `.env.example` says `SECTORS_BASE_URL=https://api.sectors.app/v1`. Confirm which version is correct before you change either one, and say so in your report. Do not silently change it.

## Red Flags (stop and fix)
- A `for symbol in universe:` loop that calls the API with no cache check.
- A cache key that includes a timestamp, so every call is a miss.
- A TTL set to `0`, or a cache that is written but never read.
- Retry loops on a 429 or 5xx response with no backoff. Retries spend credits.
- A test that uses the live key. Tests must use mock mode.
