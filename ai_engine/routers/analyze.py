from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any

from ai_engine.core.cache import AIResultCache
from ai_engine.core.data_loader import UnifiedDataLoader
from ai_engine.models.forecast.forecast_model import ForecastModel
from ai_engine.models.anomaly.isolation_forest import AnomalyModel
from ai_engine.models.peers.peer_analysis import PeerAnalysisModel
from ai_engine.models.peers.what_changed import WhatChangedModel
from ai_engine.models.smart_money.smart_money_model import SmartMoneyModel
from ai_engine.models.catalyst.catalyst_detector import CatalystDetector
from ai_engine.models.screener.screener import IntelligenceScreener, ScreenerRequest

router = APIRouter(prefix="/api/v1", tags=["analyze"])
_ai_cache = AIResultCache(ttl_seconds=3600)

class AnalyzeRequest(BaseModel):
    symbol: str
    include_forecast: bool = True
    include_anomaly: bool = True
    include_divergence: bool = True
    include_smart_money: bool = True
    include_catalysts: bool = True

def get_data_loader():
    # In a real app, you might want to cache or reuse the data loader 
    # depending on how connections to providers are managed
    return UnifiedDataLoader()

@router.post("/analyze")
async def analyze_stock(request: AnalyzeRequest, data_loader: UnifiedDataLoader = Depends(get_data_loader)):
    symbol = request.symbol.upper()
    
    # Check AI Result Cache
    cached_result = _ai_cache.get(
        symbol,
        request.include_forecast,
        request.include_anomaly,
        request.include_divergence,
        request.include_smart_money,
        request.include_catalysts
    )
    if cached_result is not None:
        return {**cached_result, "cached": True}
    
    # Initialize response structure
    response = {
        "symbol": symbol,
        "forecast": None,
        "fundamental_divergence": None,
        "divergence_signal": None,
        "opportunity_signal": None,
        "risk_signal": None,
        "anomaly": None,
        "smart_money": None,
        "catalysts": None
    }
    
    try:
        # 1. Forecast & Signals
        if request.include_forecast:
            forecast_model = ForecastModel(data_loader)
            forecast_result = forecast_model.analyze(symbol)
            if forecast_result.get("status") == "success":
                response["forecast"] = forecast_result.get("forecast")
                response["opportunity_signal"] = forecast_result.get("opportunity_signal")
                response["risk_signal"] = forecast_result.get("risk_signal")
                # The opportunity/risk signals are scored on this detection, so it is
                # the one the UI must show (peer divergence_score below is a distance).
                response["divergence_signal"] = forecast_result.get("fundamental_divergence")
            else:
                response["forecast"] = {"error": "Forecast analysis failed"}

        # 2. Fundamental Divergence / Peers
        if request.include_divergence:
            peer_model = PeerAnalysisModel(data_loader)
            peer_result = peer_model.analyze(symbol)
            what_changed_model = WhatChangedModel(data_loader)
            changes_result = what_changed_model.analyze(symbol)
            
            if peer_result.get("status") == "success":
                response["fundamental_divergence"] = {
                    "peers_context": peer_result.get("peers_context"),
                    "valuation_context": peer_result.get("valuation_context"),
                    "divergence_score": peer_result.get("divergence_score"),
                    "relative_positions": peer_result.get("relative_positions"),
                    "significant_changes": changes_result.get("significant_changes", [])
                }
            else:
                response["fundamental_divergence"] = {"error": "Divergence analysis failed"}

        # 3. Anomaly Detection
        if request.include_anomaly:
            anomaly_model = AnomalyModel(data_loader)
            anomaly_result = anomaly_model.analyze(symbol)
            response["anomaly"] = anomaly_result

        # 4. Smart Money
        if request.include_smart_money:
            sm_model = SmartMoneyModel(data_loader)
            response["smart_money"] = sm_model.analyze(symbol)

        # 5. Catalyst Detector
        if request.include_catalysts:
            cat_model = CatalystDetector(data_loader)
            response["catalysts"] = cat_model.analyze(symbol)

        _ai_cache.set(
            symbol,
            request.include_forecast,
            request.include_anomaly,
            request.include_divergence,
            request.include_smart_money,
            request.include_catalysts,
            response
        )
        return {**response, "cached": False}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/screener")
async def run_screener(request: ScreenerRequest, data_loader: UnifiedDataLoader = Depends(get_data_loader)):
    try:
        screener = IntelligenceScreener(data_loader)
        result = screener.screen(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class SummaryRequest(BaseModel):
    ticker: str
    include: Optional[list[str]] = None

from ai_engine.models.ai_summary.summary_service import SummaryService
# Use a separate cache for summaries to avoid overlapping with basic AI result cache
_summary_cache = AIResultCache(ttl_seconds=3600)

@router.post("/summary")
async def generate_summary(request: SummaryRequest, data_loader: UnifiedDataLoader = Depends(get_data_loader)):
    try:
        symbol = request.ticker.upper()
        cache_key_tuple = (symbol, str(request.include))
        
        # Check cache
        cached_result = _summary_cache.get(*cache_key_tuple)
        if cached_result is not None:
            return {**cached_result, "cached": True}
            
        summary_service = SummaryService(data_loader)
        result = summary_service.generate_summary(symbol, request.include)
        
        if result.get("status") == "SUCCESS":
            _summary_cache.set(symbol, str(request.include), result)
            return {**result, "cached": False}
        else:
            raise HTTPException(status_code=500, detail=result.get("message", "Unknown error"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
