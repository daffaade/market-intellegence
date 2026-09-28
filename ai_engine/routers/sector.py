from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any

from ai_engine.core.cache import AIResultCache
from ai_engine.core.data_loader import UnifiedDataLoader
from ai_engine.models.sector.sector_intelligence import SectorIntelligenceModel

router = APIRouter(prefix="/api/v1/sector", tags=["sector"])
_sector_cache = AIResultCache(ttl_seconds=86400) # 24h cache

def get_data_loader():
    return UnifiedDataLoader()

@router.get("/{sector_name}")
async def analyze_sector(sector_name: str, data_loader: UnifiedDataLoader = Depends(get_data_loader)):
    cached_result = _sector_cache.get(sector_name)
    if cached_result is not None:
        return {**cached_result, "cached": True}
    
    try:
        model = SectorIntelligenceModel(data_loader)
        result = model.analyze_sector(sector_name)
        
        _sector_cache.set(sector_name, result)
        return {**result, "cached": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
