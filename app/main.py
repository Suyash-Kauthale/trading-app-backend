# app/main.py

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List

from app.database import get_db, init_db
from app.models import User, Trade, Holding
from app.schemas import (
    UserRegister, UserLogin, TokenResponse, UserResponse,
    BuyRequest, SellRequest, TradeResponse, PortfolioResponse,
    PriceResponse, ChartResponse, TradingSignalResponse, HoldingResponse
)
from app.auth import (
    hash_password, verify_password, create_access_token,
    get_current_user_id
)
from app.utils.market_utils import MarketDataManager
from app.utils.trading_signals import TradingSignalGenerator
from app.routes.api_ai import router as ai_router
from app.routes.llm_chat import router as llm_router
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI app
app = FastAPI(
    title="Multi-Horizon Trading Dashboard API",
    description="Trading app with multi-horizon signals and portfolio management",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(ai_router)
app.include_router(llm_router)
# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()




# ============ AUTH ENDPOINTS ============

@app.post("/api/auth/register", response_model=TokenResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user with initial balance of ₹100,000"""
    
    # Check if user exists
    existing_user = db.query(User).filter(
        User.username == user_data.username
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        balance=100000.0  # Initial balance ₹100,000
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create JWT token
    access_token = create_access_token(data={"user_id": user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username
    }

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login with username and password"""
    
    user = db.query(User).filter(User.username == credentials.username).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    access_token = create_access_token(data={"user_id": user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username
    }

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get current user details"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

# ============ PORTFOLIO ENDPOINTS ============

@app.get("/api/portfolio/balance")
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

@app.get("/api/portfolio/trades")
async def get_trade_history(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get user trade history"""
    
    trades = db.query(Trade).filter(Trade.user_id == user_id).order_by(Trade.created_at.desc()).all()
    
    return {
        "total_trades": len(trades),
        "trades": [TradeResponse.from_orm(t) for t in trades]
    }

# ============ TRADING ENDPOINTS ============

@app.post("/api/trading/buy", response_model=TradeResponse)
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
    
    return TradeResponse.from_orm(trade)

@app.post("/api/trading/sell", response_model=TradeResponse)
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
    
    return TradeResponse.from_orm(trade)

# ============ MARKET DATA ENDPOINTS ============

@app.get("/api/market/price/{symbol}", response_model=PriceResponse)
async def get_price(symbol: str):
    """Get current price for a symbol"""
    
    data = MarketDataManager.get_current_price(symbol.upper())
    
    if "error" in data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=data["error"]
        )
    
    return PriceResponse(**data)

@app.get("/api/market/chart/{symbol}", response_model=ChartResponse)
async def get_chart(symbol: str, period: str = "1mo"):
    """Get OHLCV chart data"""
    
    chart_data = MarketDataManager.get_historical_data(symbol.upper(), period)
    
    if not chart_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No data found for {symbol}"
        )
    
    return ChartResponse(symbol=symbol.upper(), data=chart_data, period=period)

@app.get("/api/market/intraday/{symbol}")
async def get_intraday(symbol: str, interval: str = "15m"):
    """Get intraday chart data"""
    
    chart_data = MarketDataManager.get_intraday_data(symbol.upper(), interval)
    
    if not chart_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No intraday data found for {symbol}"
        )
    
    return {
        "symbol": symbol.upper(),
        "data": chart_data,
        "interval": interval
    }

@app.get("/api/market/search")
async def search_stocks(query: str):
    """Search for stocks"""
    
    results = MarketDataManager.search_symbols(query)
    
    return {
        "query": query,
        "results": results
    }

# ============ ANALYTICS & SIGNALS ============

@app.post("/api/trading/signals/{symbol}", response_model=TradingSignalResponse)
async def generate_signals(symbol: str):
    """Generate multi-horizon trading signals"""
    
    # Get current price
    price_data = MarketDataManager.get_current_price(symbol.upper())
    if "error" in price_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=price_data["error"]
        )
    
    current_price = price_data["current_price"]
    
    # Get historical data
    historical_data = MarketDataManager.get_historical_data(symbol.upper(), period="3mo")
    
    if not historical_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to fetch historical data"
        )
    
    # Generate signals
    signals = TradingSignalGenerator.generate_signals(
        symbol.upper(),
        current_price,
        historical_data
    )
    
    return TradingSignalResponse(**signals)

# ============ TRADE PLAN ENDPOINT ============

@app.post("/api/trade/plan")
async def generate_trade_plan(
    data: dict,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Generate consolidated trade plan"""
    
    symbol = data.get("symbol", "RELIANCE")
    
    # Get signals
    price_data = MarketDataManager.get_current_price(symbol)
    historical_data = MarketDataManager.get_historical_data(symbol, period="3mo")
    
    if not historical_data:
        return {"error": "Unable to fetch data"}
    
    signals = TradingSignalGenerator.generate_signals(symbol, price_data["current_price"], historical_data)
    
    return signals

# ============ HEALTH CHECK ============

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Multi-Horizon Trading API is running"
    }

# ============ PNL-HISTORY ============
@app.get("/api/portfolio/pnl-history")
async def get_pnl_history(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get portfolio P&L history for charting"""
    
    trades = db.query(Trade).filter(Trade.user_id == user_id).order_by(Trade.created_at).all()
    
    running_pnl = 0
    pnl_history = []
    
    for trade in trades:
        if trade.trade_type == "BUY":
            # Cost of buy
            running_pnl -= trade.total_value
        elif trade.trade_type == "SELL":
            # Revenue from sell
            running_pnl += trade.total_value
        
        pnl_history.append({
            "timestamp": trade.created_at.isoformat(),
            "pnl": round(running_pnl, 2),
            "symbol": trade.symbol,
            "type": trade.trade_type
        })
    
    return {"pnl_history": pnl_history}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)