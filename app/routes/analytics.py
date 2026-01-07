# app/routes/analytics.py

"""
Trading analytics and signals routes

Endpoints:
- POST /api/trading/signals/{symbol} - Get multi-horizon trading signals
- POST /api/trade/plan - Generate consolidated trade plan
"""

from fastapi import APIRouter, HTTPException
from app.schemas import TradingSignalResponse
from app.utils import MarketDataManager, TradingSignalGenerator

router = APIRouter(tags=["analytics"])

@router.post("/api/trading/signals/{symbol}", response_model=TradingSignalResponse)
async def generate_signals(symbol: str):
    """Generate multi-horizon trading signals"""
    
    # Get current price
    price_data = MarketDataManager.get_current_price(symbol.upper())
    if "error" in price_data:
        raise HTTPException(
            status_code=404,
            detail=price_data["error"]
        )
    
    current_price = price_data["current_price"]
    
    # Get historical data
    historical_data = MarketDataManager.get_historical_data(symbol.upper(), period="3mo")
    
    if not historical_data:
        raise HTTPException(
            status_code=400,
            detail="Unable to fetch historical data"
        )
    
    # Generate signals
    signals = TradingSignalGenerator.generate_signals(
        symbol.upper(),
        current_price,
        historical_data
    )
    
    return TradingSignalResponse(**signals)

@router.post("/api/trade/plan")
async def generate_trade_plan(data: dict):
    """Generate consolidated trade plan"""
    
    symbol = data.get("symbol", "RELIANCE")
    
    # Get signals
    price_data = MarketDataManager.get_current_price(symbol)
    historical_data = MarketDataManager.get_historical_data(symbol, period="3mo")
    
    if not historical_data:
        return {"error": "Unable to fetch data"}
    
    signals = TradingSignalGenerator.generate_signals(symbol, price_data["current_price"], historical_data)
    
    return signals