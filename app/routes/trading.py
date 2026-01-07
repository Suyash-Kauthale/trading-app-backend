# app/routes/trading.py

"""
Trading routes for buy/sell operations

Endpoints:
- POST /api/trading/buy - Buy stocks
- POST /api/trading/sell - Sell stocks
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Trade, Holding
from app.schemas import BuyRequest, SellRequest, TradeResponse
from app.auth import get_current_user_id

router = APIRouter(prefix="/api/trading", tags=["trading"])

@router.post("/buy", response_model=TradeResponse)
async def buy_stock(
    request: BuyRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Buy stock and create holding"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    total_cost = request.quantity * request.price
    
    # Check if user has enough balance
    if user.balance < total_cost:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient balance. Required: ₹{total_cost}, Available: ₹{user.balance}"
        )
    
    # Deduct from user balance
    user.balance -= total_cost
    
    # Update or create holding
    existing_holding = db.query(Holding).filter(
        Holding.user_id == user_id,
        Holding.symbol == request.symbol
    ).first()
    
    if existing_holding:
        # Average price calculation
        total_quantity = existing_holding.quantity + request.quantity
        existing_holding.average_price = (
            (existing_holding.average_price * existing_holding.quantity + 
             request.price * request.quantity) / total_quantity
        )
        existing_holding.quantity = total_quantity
        existing_holding.current_price = request.price
    else:
        new_holding = Holding(
            user_id=user_id,
            symbol=request.symbol,
            quantity=request.quantity,
            average_price=request.price,
            current_price=request.price
        )
        db.add(new_holding)
    
    # Create trade record
    trade = Trade(
        user_id=user_id,
        symbol=request.symbol,
        trade_type="BUY",
        quantity=request.quantity,
        price=request.price,
        total_value=total_cost,
        entry_price=request.entry_price,
        stop_loss=request.stop_loss,
        target=request.target,
        status="OPEN"
    )
    
    db.add(trade)
    db.commit()
    db.refresh(trade)
    
    return trade

@router.post("/sell", response_model=TradeResponse)
async def sell_stock(
    request: SellRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Sell stock from holding"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user has the holding
    holding = db.query(Holding).filter(
        Holding.user_id == user_id,
        Holding.symbol == request.symbol
    ).first()
    
    if not holding or holding.quantity < request.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient holding. Available: {holding.quantity if holding else 0}"
        )
    
    total_revenue = request.quantity * request.price
    
    # Add to user balance
    user.balance += total_revenue
    
    # Update holding
    holding.quantity -= request.quantity
    if holding.quantity == 0:
        db.delete(holding)
    
    # Create trade record
    trade = Trade(
        user_id=user_id,
        symbol=request.symbol,
        trade_type="SELL",
        quantity=request.quantity,
        price=request.price,
        total_value=total_revenue,
        status="CLOSED"
    )
    
    db.add(trade)
    db.commit()
    db.refresh(trade)
    
    return trade