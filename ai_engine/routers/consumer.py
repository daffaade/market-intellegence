from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from ai_engine.core.cache import AIResultCache
from ai_engine.models.consumer_behavior.consumer_behavior_model import ConsumerBehaviorModel

router = APIRouter(prefix="/api/v1/consumer-behavior", tags=["consumer-behavior"])
_consumer_cache = AIResultCache(ttl_seconds=3600)

class ConsumerBehaviorRequest(BaseModel):
    keyword: str
    industry: str

@router.post("/analyze")
async def analyze_consumer_behavior(request: ConsumerBehaviorRequest):
    keyword = request.keyword.lower().strip()
    industry = request.industry.lower().strip()
    cache_key = f"{keyword}_{industry}"
    
    cached_result = _consumer_cache.get(cache_key)
    if cached_result is not None:
        return {**cached_result, "cached": True}
        
    try:
        model = ConsumerBehaviorModel()
        result = model.analyze(keyword=keyword, industry=industry)
        
        # Store result in cache
        _consumer_cache.set(cache_key, result)
        return {**result, "cached": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
