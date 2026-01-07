# app/routes/portfolio.py

"""
Portfolio management routes

Endpoints:
- GET /api/portfolio/balance - Get user balance and holdings
- GET /api/portfolio/trades - Get trade history
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Holding, Trade
from app.schemas import PortfolioResponse, HoldingResponse, TradeHistoryResponse
from app.auth import get_current_user_id
from app.utils import MarketDataManager

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])

@router.get("/balance", response_model=PortfolioResponse)
async def get_portfolio(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get user portfolio with balance and holdings"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get all holdings
    holdings = db.query(Holding).filter(Holding.user_id == user_id).all()
    
    # Calculate portfolio value
    portfolio_value = 0
    total_pnl = 0
    holdings_response = []
    
    for holding in holdings:
        current_price_data = MarketDataManager.get_current_price(holding.symbol)
        
        if "error" not in current_price_data:
            current_price = current_price_data["current_price"]
            holding.current_price = current_price
            
            total_value = current_price * holding.quantity
            pnl = (current_price - holding.average_price) * holding.quantity
            pnl_percentage = ((current_price - holding.average_price) / holding.average_price * 100) if holding.average_price > 0 else 0
            
            portfolio_value += total_value
            total_pnl += pnl
            
            holdings_response.append(HoldingResponse(
                id=holding.id,
                symbol=holding.symbol,
                quantity=holding.quantity,
                average_price=holding.average_price,
                current_price=current_price,
                total_value=total_value,
                pnl=pnl,
                pnl_percentage=pnl_percentage
            ))
    
    cash_balance = user.balance
    total_balance = cash_balance + portfolio_value
    total_pnl_percentage = ((total_pnl / (total_balance - total_pnl) * 100) if (total_balance - total_pnl) > 0 else 0)
    
    # Count winning/losing trades
    trades = db.query(Trade).filter(Trade.user_id == user_id).all()
    winning_trades = sum(1 for t in trades if t.status == "CLOSED" and t.total_value > 0)
    losing_trades = sum(1 for t in trades if t.status == "CLOSED" and t.total_value < 0)
    
    return PortfolioResponse(
        total_balance=round(total_balance, 2),
        cash_balance=round(cash_balance, 2),
        portfolio_value=round(portfolio_value, 2),
        total_pnl=round(total_pnl, 2),
        total_pnl_percentage=round(total_pnl_percentage, 2),
        holdings=holdings_response,
        winning_trades=winning_trades,
        losing_trades=losing_trades
    )

@router.get("/trades", response_model=TradeHistoryResponse)
async def get_trade_history(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get user trade history"""
    
    trades = db.query(Trade).filter(Trade.user_id == user_id).order_by(Trade.created_at.desc()).all()
    
    return {
        "total_trades": len(trades),
        "trades": trades
    }