from fastapi import APIRouter, HTTPException

from data_processing.data_sectors.fundamentals import get_report, map_fundamentals
from data_processing.data_sectors.market_series import get_foreign_flow

router = APIRouter(prefix="/api/v1", tags=["fundamentals"])


@router.get("/fundamentals/{symbol}")
def company_fundamentals(symbol: str):
    """Multi-year fundamentals from the Sectors report (cached 7 days on disk)."""
    symbol = symbol.replace(".JK", "").upper()
    cached = get_report(symbol)
    if not cached:
        raise HTTPException(status_code=404, detail=f"Sectors report for {symbol} is unavailable")
    out = map_fundamentals(symbol, cached["report"], cached["fetched_at"])
    # Daily net foreign flow, 90 days (cached 7 days: 1 credit per symbol per week).
    ff = get_foreign_flow(symbol)
    out["foreign_flow"] = [
        {"date": p["date"], "net_idr": p["net"], "foreign_share": p["foreign_share"]}
        for p in (ff or {}).get("points", []) if p.get("net") is not None
    ]
    return out
