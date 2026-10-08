from fastapi import APIRouter, HTTPException

from ai_engine.models.sector.sector_intelligence import SectorIntelligenceModel, sector_overview

router = APIRouter(prefix="/api/v1/sector", tags=["sector"])


@router.get("/")
def sectors():
    """All IDX sectors: relative strength vs IHSG, breadth, rotation (cached 6h)."""
    try:
        return sector_overview()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"sector data unavailable: {e}")


@router.get("/{sector_name}")
def analyze_sector(sector_name: str):
    res = SectorIntelligenceModel().analyze_sector(sector_name)
    if res.get("error"):
        raise HTTPException(status_code=404, detail=res["error"])
    return res
