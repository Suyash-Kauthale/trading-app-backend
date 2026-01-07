# app/schemas.py

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List

# ============ AUTH SCHEMAS ============

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str

# ============ USER SCHEMAS ============

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    balance: float
    created_at: datetime

    class Config:
        from_attributes = True

# ============ HOLDING SCHEMAS ============

class HoldingResponse(BaseModel):
    id: int
    symbol: str
    quantity: int
    average_price: float
    current_price: float
    total_value: float
    pnl: float
    pnl_percentage: float

    class Config:
        from_attributes = True

class PortfolioResponse(BaseModel):
    total_balance: float
    cash_balance: float
    portfolio_value: float
    total_pnl: float
    total_pnl_percentage: float
    holdings: List[HoldingResponse]
    winning_trades: int
    losing_trades: int

# ============ TRADING SCHEMAS ============

class BuyRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10)
    quantity: int = Field(..., gt=0)
    price: float = Field(..., gt=0)
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    target: Optional[float] = None

class SellRequest(BaseModel):
    symbol: str
    quantity: int = Field(..., gt=0)
    price: float = Field(..., gt=0)

class TradeResponse(BaseModel):
    id: int
    symbol: str
    trade_type: str
    quantity: int
    price: float
    total_value: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class TradeHistoryResponse(BaseModel):
    total_trades: int
    trades: List[TradeResponse]

# ============ MARKET DATA SCHEMAS ============

class PriceResponse(BaseModel):
    symbol: str
    current_price: float
    previous_close: float
    change: float
    change_percentage: float
    timestamp: datetime

class ChartData(BaseModel):
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

class ChartResponse(BaseModel):
    symbol: str
    data: List[ChartData]
    period: str = "1mo"

# ============ SIGNAL SCHEMAS ============

class SignalDetail(BaseModel):
    signal: str  # BUY, SELL, NEUTRAL
    entry: float
    stop_loss: float
    target: float
    confidence: float
    risk_reward: float

class TradingSignalResponse(BaseModel):
    symbol: str
    current_price: float
    intraday: SignalDetail
    shortterm: SignalDetail
    longterm: SignalDetail
    consolidated: SignalDetail
    timestamp: datetime

# ============ ERROR SCHEMAS ============

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None