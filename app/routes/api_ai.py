# app/routes/api_ai.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai_agent import AdvancedTradingAI
from app.auth import get_current_user_id
from app.database import get_db
from app.models import User


router = APIRouter(prefix="/api/ai", tags=["ai"])


class AIAnalysisRequest(BaseModel):
    symbol: str
    mode: str = "long"  # "long" or "intraday"


@router.post("/analyze")
async def ai_analyze(
    request: AIAnalysisRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Analyze stock with selectable mode: long-term or intraday.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        # Add .NS suffix for Indian stocks if not already present
        symbol = request.symbol.upper()
        if not symbol.endswith(('.NS', '.BO', '.BSE', '.NSE')):
            symbol = f"{symbol}.NS"  # Default to NSE
        
        ai = AdvancedTradingAI(symbol)
        ai.fetch_data(mode=request.mode)  # "long" or "intraday"
        ai.add_indicators()
        ai.train()
        
        # Get raw prediction
        pred = ai.predict_raw()
        
        # Generate all insights
        result = {
            "symbol": symbol,
            "mode": request.mode,
            "signal": pred["direction"],
            "confidence": round(pred["confidence"] * 100, 2),
            "current_price": round(pred["current_price"], 2),
            
            # Reason: why buy/sell?
            "reason": ai.explain_why(pred),
            
            # Position sizing: how many to buy?
            "position_recommendation": ai.suggest_position_size(
                pred, 
                account_balance=user.balance
            ),
            
            # Strategy: when/how to trade?
            "strategy": ai.next_strategy(pred),
            
            # Raw indicators
            "indicators": {
                "rsi": round(pred["rsi"], 2),
                "sma_10": round(pred["sma_10"], 2),
                "volatility": round(pred["volatility"], 4),
            }
        }
        
        return result
        
    except ValueError as e:
        # Handle "Not enough data" error gracefully
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Analysis failed: {str(e)}")
