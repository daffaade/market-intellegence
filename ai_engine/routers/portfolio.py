from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
import pandas as pd

from ai_engine.core.cache import AIResultCache
from ai_engine.core.data_loader import UnifiedDataLoader
from ai_engine.models.portofolio_risk.portofolio_risk import PortfolioRisk

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])
_portfolio_cache = AIResultCache(ttl_seconds=3600)

class PortfolioAsset(BaseModel):
    ticker: str
    weight: float

class PortfolioRiskRequest(BaseModel):
    portfolio: List[PortfolioAsset]
    period: str = "1y"

def get_data_loader():
    return UnifiedDataLoader()

def create_fetch_prices(data_loader: UnifiedDataLoader):
    def fetch_prices(ticker: str, period: str):
        df = data_loader.get_historical_data(ticker, period)
        if df is not None and not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                s = df['Close'].iloc[:, 0]
            else:
                s = df['Close']
            if isinstance(s, pd.DataFrame):
                s = s.squeeze()
            return s
        return None
    return fetch_prices

@router.post("/risk")
async def calculate_portfolio_risk(request: PortfolioRiskRequest, data_loader: UnifiedDataLoader = Depends(get_data_loader)):
    # Create cache key based on portfolio composition and period
    # Sort the portfolio to ensure identical compositions get same cache key
    sorted_portfolio = sorted([{"ticker": p.ticker.upper(), "weight": p.weight} for p in request.portfolio], key=lambda x: x["ticker"])
    cache_key_tuple = (str(sorted_portfolio), request.period)
    
    cached_result = _portfolio_cache.get(*cache_key_tuple)
    if cached_result is not None:
        return {**cached_result, "cached": True}
        
    try:
        fetch_prices = create_fetch_prices(data_loader)
        model = PortfolioRisk(data_fetcher=fetch_prices)
        
        result = model.calculate_risk(portfolio=sorted_portfolio, period=request.period)
        
        if result.get("status") == "SUCCESS":
            _portfolio_cache.set(str(sorted_portfolio), request.period, result)
            return {**result, "cached": False}
        else:
            raise HTTPException(status_code=400, detail=result.get("message", "Unknown error"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
