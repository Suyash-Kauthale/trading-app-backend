# app/routes/market_data.py

"""
Market data routes for real-time stock information

Endpoints:
- GET /api/market/price/{symbol} - Get current price
- GET /api/market/chart/{symbol} - Get historical data
- GET /api/market/intraday/{symbol} - Get intraday data
- GET /api/market/search - Search stocks
"""

from fastapi import APIRouter, HTTPException
from app.schemas import PriceResponse, ChartResponse
from app.utils import MarketDataManager

router = APIRouter(prefix="/api/market", tags=["market"])

@router.get("/price/{symbol}", response_model=PriceResponse)
async def get_price(symbol: str):
    """Get current price for a symbol"""
    
    data = MarketDataManager.get_current_price(symbol.upper())
    
    if "error" in data:
        raise HTTPException(
            status_code=404,
            detail=data["error"]
        )
    
    return PriceResponse(**data)

@router.get("/chart/{symbol}", response_model=ChartResponse)
async def get_chart(symbol: str, period: str = "1mo"):
    """Get OHLCV chart data"""
    
    chart_data = MarketDataManager.get_historical_data(symbol.upper(), period)
    
    if not chart_data:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for {symbol}"
        )
    
    return ChartResponse(symbol=symbol.upper(), data=chart_data, period=period)

@router.get("/intraday/{symbol}")
async def get_intraday(symbol: str, interval: str = "15m"):
    """Get intraday chart data"""
    
    chart_data = MarketDataManager.get_intraday_data(symbol.upper(), interval)
    
    if not chart_data:
        raise HTTPException(
            status_code=404,
            detail=f"No intraday data found for {symbol}"
        )
    
    return {
        "symbol": symbol.upper(),
        "data": chart_data,
        "interval": interval
    }

@router.get("/search")
async def search_stocks(query: str):
    """Search for stocks"""
    
    results = MarketDataManager.search_symbols(query)
    
    return {
        "query": query,
        "results": results
    }