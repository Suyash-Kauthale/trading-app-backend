# 📊 Multi-Horizon Trading Dashboard - Complete Backend

**A production-ready trading application with user authentication, real-time market data, and multi-horizon trading signals.**

---

## ✨ Key Features

✅ **User Authentication** - Secure JWT-based login/registration  
✅ **Initial Balance** - Every user starts with ₹100,000  
✅ **Real-time Trading** - Buy/sell stocks with simulated execution  
✅ **Portfolio Tracking** - Real-time P&L, holdings, and balance  
✅ **Trading Signals** - Multi-horizon analysis (Intraday, Short-term, Long-term)  
✅ **Market Data** - Real-time prices via yFinance API  
✅ **OHLCV Charts** - Historical data for technical analysis  
✅ **Trade History** - Complete transaction records  
✅ **Conflict Resolution** - Consolidated signals when horizons disagree  
✅ **Risk Management** - Position sizing and R:R calculations  

---

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python 3.10+)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: JWT tokens with bcrypt password hashing
- **Market Data**: yFinance API (real-time stock prices)
- **API Docs**: Swagger UI + ReDoc
- **Deployment**: Docker-ready, Gunicorn-compatible

---

## 📋 Quick Start (5 minutes)

### 1. Clone & Setup
```bash
mkdir trading-app-backend
cd trading-app-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Server
```bash
python run.py
```

Server running at: **http://localhost:8000**  
API Documentation: **http://localhost:8000/docs**

### 3. Test API
```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "trader1",
    "email": "trader@example.com",
    "password": "Pass@123"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"trader1","password":"Pass@123"}'
```

---

## 📁 Project Structure

```
trading-app-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application
│   ├── database.py                # SQLite setup
│   ├── models.py                  # Database models
│   ├── schemas.py                 # Pydantic schemas
│   ├── auth.py                    # JWT authentication
│   ├── routes/
│   │   └── __init__.py
│   └── utils/
│       ├── __init__.py
│       ├── market_utils.py        # yFinance integration
│       └── trading_signals.py     # Signal generation
│
├── requirements.txt               # Python dependencies
├── .env                           # Environment variables
├── run.py                         # Entry point
├── Dockerfile                     # Docker configuration
└── README.md                      # This file
```

---

## 🔌 API Endpoints

### Authentication
```
POST   /api/auth/register     - Create account (₹100,000 balance)
POST   /api/auth/login        - Login & get JWT token
GET    /api/auth/me           - Get current user info
```

### Portfolio Management
```
GET    /api/portfolio/balance - Get balance, holdings, P&L
GET    /api/portfolio/trades  - Get trade history
```

### Trading Operations
```
POST   /api/trading/buy       - Buy stocks
POST   /api/trading/sell      - Sell stocks
```

### Market Data
```
GET    /api/market/price/{symbol}      - Current price
GET    /api/market/chart/{symbol}      - Historical OHLCV data
GET    /api/market/intraday/{symbol}   - Intraday data
GET    /api/market/search?query={q}    - Search stocks
```

### Trading Analysis
```
POST   /api/trading/signals/{symbol}   - Get multi-horizon signals
POST   /api/trade/plan                 - Generate trade plan
```

---

## 💾 Database Models

### Users Table
- `id` - Primary key
- `username` - Unique username
- `password_hash` - Hashed password
- `email` - User email
- `balance` - Cash balance (₹100,000 initial)
- `created_at` - Account creation date
- `is_active` - Account status

### Holdings Table
- `id` - Primary key
- `user_id` - Foreign key to users
- `symbol` - Stock symbol (e.g., RELIANCE)
- `quantity` - Shares held
- `average_price` - Cost basis
- `current_price` - Latest price from yFinance

### Trades Table
- `id` - Primary key
- `user_id` - Foreign key
- `symbol` - Stock symbol
- `trade_type` - BUY or SELL
- `quantity` - Number of shares
- `price` - Execution price
- `total_value` - Quantity × Price
- `status` - OPEN, CLOSED, PARTIAL
- `entry_price`, `stop_loss`, `target` - Trade plan

---

## 🔐 Authentication Flow

```
1. User Registration
   ↓
   Backend hashes password (bcrypt)
   Creates user with ₹100,000 balance
   Returns JWT token

2. User Login
   ↓
   Backend verifies credentials
   Returns JWT token

3. Protected Routes
   ↓
   User sends token in Authorization header
   Backend validates token
   Executes request if valid
```

### Example: Using JWT Token
```javascript
const token = "eyJhbGciOiJIUzI1NiIs...";

fetch("http://localhost:8000/api/portfolio/balance", {
  headers: {
    "Authorization": `Bearer ${token}`
  }
})
```

---

## 📊 Trading Signals Explained

### Intraday (0-24 Hours)
- **Strategy**: RSI-based (overbought/oversold)
- **Confidence**: 75-80%
- **Use Case**: Quick day trades

### Short-term (1-4 Weeks)
- **Strategy**: Moving Average Crossover
- **Confidence**: 82-85% (highest weight)
- **Use Case**: Swing trading

### Long-term (Months-Years)
- **Strategy**: Trend analysis + SMA
- **Confidence**: 80-82%
- **Use Case**: Position trading

### Consolidated Signal
- **Calculation**: Weighted average of all three
- **Conflict Resolution**: Majority vote + weighted confidence
- **Risk:Reward**: Blended across all horizons

---

## 💰 Trading Simulation Example

```
User Registration
├─ Balance: ₹100,000

Buy 10 RELIANCE @ ₹2,850
├─ Cost: ₹28,500
├─ New Balance: ₹71,500
├─ Holding: 10 RELIANCE @ ₹2,850 avg

Price moves to ₹2,900
├─ Holding Value: ₹29,000
├─ Unrealized P&L: ₹500
├─ P&L %: 1.75%

Sell 5 RELIANCE @ ₹2,900
├─ Revenue: ₹14,500
├─ New Balance: ₹86,000
├─ Realized P&L: ₹250
├─ Trade Status: CLOSED

Remaining Holding
├─ 5 RELIANCE @ ₹2,850 avg
├─ Current Value: ₹14,500
├─ Unrealized P&L: ₹250
```

---

## 🚀 Deployment

### Docker Deployment
```bash
# Build image
docker build -t trading-app:latest .

# Run container
docker run -p 8000:8000 trading-app:latest
```

### Production Deployment (Gunicorn)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app.main:app
```

### Environment Variables (.env)
```
SECRET_KEY=your-secret-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
DATABASE_URL=sqlite:///./trading_app.db
CORS_ORIGINS=["http://localhost:3000"]
```

---

## 📈 Real-time Updates

### Update Portfolio Every 5 Seconds
```python
import asyncio

async def update_portfolio():
    while True:
        # Fetch portfolio
        # Fetch current prices
        # Recalculate P&L
        await asyncio.sleep(5)
```

### WebSocket Support (Future)
```javascript
const ws = new WebSocket("ws://localhost:8000/ws/portfolio");
ws.onmessage = (event) => {
  const portfolio = JSON.parse(event.data);
  updateUI(portfolio);
};
```

---

## 🧪 Testing

### Unit Testing Template
```python
import pytest
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_register():
    response = client.post("/api/auth/register", json={
        "username": "test",
        "email": "test@test.com",
        "password": "Pass@123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
```

### Run Tests
```bash
pytest tests/ -v
```

---

## 🔧 Configuration

### Change Initial Balance
Edit `app/main.py` → `register()`:
```python
balance=100000.0  # Change this
```

### Add More Stocks
Edit `app/utils/market_utils.py`:
```python
VALID_SYMBOLS = [
    'RELIANCE', 'INFY', 'TCS', 'WIPRO',  # Add more
]
```

### Adjust Signal Logic
Edit `app/utils/trading_signals.py`:
```python
# Change RSI levels
if rsi < 30:  # Change threshold
    signal = "BUY"
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 8000 in use | `lsof -i :8000` and kill process |
| Module not found | Activate venv and reinstall deps |
| CORS errors | Check frontend URL in CORS config |
| Token expired | User must login again |
| No market data | Check internet, yFinance rate limit |

---

## 📚 API Documentation

Interactive API docs available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

All endpoints documented with request/response examples.

---

## 🎯 Next Steps

1. Start backend server
2. Test all endpoints via http://localhost:8000/docs
3. Integrate frontend (React, Vue, etc.)
4. Add WebSocket for real-time updates
5. Implement advanced features (ML, backtesting, alerts)

---

## 📞 Support & Documentation

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **yFinance Docs**: https://github.com/ranaroussi/yfinance
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/

---

## 📝 Version History

- **v1.0.0** (2025-12-20)
  - Initial release
  - Core trading functionality
  - Multi-horizon signals
  - Real-time market data

---

## 👨‍💼 Contributing

For improvements or bug reports, please open an issue or submit a PR.

---

## 📄 License

This project is open source and available for educational purposes.

---

## 🙏 Acknowledgments

- Built with FastAPI, SQLAlchemy, yFinance
- Designed for VIT Pune FF-180 Project
- Team: Suyash, Yash, Om, Mahesh, Kedar

---

**Status**: ✅ Production-Ready | Version: 1.0.0 | Last Updated: Dec 20, 2025

Happy Trading! 📈