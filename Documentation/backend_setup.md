# Multi-Horizon Trading App - Backend Setup Guide

## Project Structure

```
trading-app-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── database.py             # SQLite database setup
│   ├── models.py               # SQLAlchemy models
│   ├── schemas.py              # Pydantic schemas
│   ├── auth.py                 # JWT authentication
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py             # Login/Register routes
│   │   ├── portfolio.py        # Portfolio management
│   │   ├── trading.py          # Trading routes (buy/sell)
│   │   ├── market_data.py      # Real-time stock data
│   │   └── analytics.py        # Trading signals & analytics
│   └── utils/
│       ├── __init__.py
│       ├── trading_signals.py  # Signal generation logic
│       └── market_utils.py     # yFinance integration
├── requirements.txt
├── .env
└── run.py
```

## Installation & Setup

### 1. Create Virtual Environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Server
```bash
python run.py
```

Server runs at: `http://localhost:8000`
API Docs: `http://localhost:8000/docs`

## Key Features

✅ **User Authentication**: Register → Login → JWT tokens  
✅ **Portfolio Management**: Initial ₹100,000 balance, buy/sell stocks  
✅ **Real-time Stock Data**: yFinance API integration  
✅ **Trading Signals**: Multi-horizon analysis (Intraday, Short-term, Long-term)  
✅ **Chart Data**: OHLCV data for frontend charts  
✅ **Risk Management**: Position sizing, P&L calculations  
✅ **Trade History**: Track all transactions  

## API Endpoints

### Authentication
- `POST /api/auth/register` - Create new account
- `POST /api/auth/login` - Login with credentials
- `POST /api/auth/logout` - Logout

### Portfolio
- `GET /api/portfolio/balance` - Check balance & holdings
- `GET /api/portfolio/trades` - Trade history

### Trading
- `POST /api/trading/buy` - Buy stock
- `POST /api/trading/sell` - Sell stock

### Market Data
- `GET /api/market/price/{symbol}` - Current price
- `GET /api/market/chart/{symbol}` - OHLCV chart data
- `GET /api/market/search` - Search stocks

### Trading Analysis
- `POST /api/trading/signals/{symbol}` - Generate trade signals
