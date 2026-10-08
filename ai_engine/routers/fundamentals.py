from fastapi import APIRouter, HTTPException

from data_processing.data_sectors.fundamentals import get_report, map_fundamentals

router = APIRouter(prefix="/api/v1", tags=["fundamentals"])


@router.get("/fundamentals/{symbol}")
def company_fundamentals(symbol: str):
    """Multi-year fundamentals from the Sectors report (cached 7 days on disk)."""
    symbol = symbol.replace(".JK", "").upper()
    cached = get_report(symbol)
    if not cached:
        raise HTTPException(status_code=404, detail=f"Sectors report for {symbol} is unavailable")
    return map_fundamentals(symbol, cached["report"], cached["fetched_at"])
