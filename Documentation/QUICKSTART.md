# QUICK START GUIDE - Trading App Backend

## 🚀 Installation & Setup (5 minutes)

### Step 1: Create Project Structure
```bash
mkdir trading-app-backend
cd trading-app-backend
mkdir app app/routes app/utils
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Create Required Files
Copy all provided files into appropriate directories:
```
trading-app-backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── auth.py
│   ├── routes/
│   │   └── __init__.py
│   └── utils/
│       ├── __init__.py
│       ├── market_utils.py
│       └── trading_signals.py
├── requirements.txt
├── .env
└── run.py
```

### Step 5: Run the Server
```bash
python run.py
```

Server will start at: **http://localhost:8000**
API Documentation: **http://localhost:8000/docs**

---

## 📋 API ENDPOINTS REFERENCE

### Authentication

#### Register New User
```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "trader123",
    "email": "trader@example.com",
    "password": "SecurePass123"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": 1,
  "username": "trader123"
}
```

#### Login
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "trader123",
    "password": "SecurePass123"
  }'
```

---

### Portfolio Management

#### Get Portfolio Balance & Holdings
```bash
curl -X GET "http://localhost:8000/api/portfolio/balance" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

Response:
```json
{
  "total_balance": 100000,
  "cash_balance": 95000,
  "portfolio_value": 5000,
  "total_pnl": 250,
  "total_pnl_percentage": 2.5,
  "holdings": [
    {
      "id": 1,
      "symbol": "RELIANCE",
      "quantity": 10,
      "average_price": 2800,
      "current_price": 2850,
      "total_value": 28500,
      "pnl": 500,
      "pnl_percentage": 1.79
    }
  ],
  "winning_trades": 5,
  "losing_trades": 2
}
```

#### Get Trade History
```bash
curl -X GET "http://localhost:8000/api/portfolio/trades" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

### Trading Operations

#### Buy Stock
```bash
curl -X POST "http://localhost:8000/api/trading/buy" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "RELIANCE",
    "quantity": 10,
    "price": 2850.50,
    "entry_price": 2850,
    "stop_loss": 2750,
    "target": 3000
  }'
```

#### Sell Stock
```bash
curl -X POST "http://localhost:8000/api/trading/sell" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "RELIANCE",
    "quantity": 5,
    "price": 2900
  }'
```

---

### Market Data

#### Get Current Price
```bash
curl -X GET "http://localhost:8000/api/market/price/RELIANCE"
```

Response:
```json
{
  "symbol": "RELIANCE",
  "current_price": 2850.50,
  "previous_close": 2840.00,
  "change": 10.50,
  "change_percentage": 0.37,
  "timestamp": "2025-12-20T13:30:00"
}
```

#### Get Chart Data (Last 1 month)
```bash
curl -X GET "http://localhost:8000/api/market/chart/RELIANCE?period=1mo"
```

#### Get Intraday Data (15-min intervals)
```bash
curl -X GET "http://localhost:8000/api/market/intraday/RELIANCE?interval=15m"
```

#### Search Stocks
```bash
curl -X GET "http://localhost:8000/api/market/search?query=REL"
```

---

### Trading Signals & Analytics

#### Generate Multi-Horizon Signals
```bash
curl -X POST "http://localhost:8000/api/trading/signals/RELIANCE"
```

Response:
```json
{
  "symbol": "RELIANCE",
  "current_price": 2850.50,
  "intraday": {
    "signal": "BUY",
    "entry": 2848.00,
    "stop_loss": 2775.00,
    "target": 2905.00,
    "confidence": 78,
    "risk_reward": 2.14
  },
  "shortterm": {
    "signal": "BUY",
    "entry": 2835.50,
    "stop_loss": 2750.00,
    "target": 2950.00,
    "confidence": 85,
    "risk_reward": 2.67
  },
  "longterm": {
    "signal": "BUY",
    "entry": 2850.50,
    "stop_loss": 2650.50,
    "target": 3250.50,
    "confidence": 82,
    "risk_reward": 3.0
  },
  "consolidated": {
    "signal": "BUY",
    "entry": 2840.25,
    "stop_loss": 2790.00,
    "target": 3100.00,
    "confidence": 82,
    "risk_reward": 2.6
  },
  "timestamp": "2025-12-20T13:30:00"
}
```

---

## 🔧 Configuration & Customization

### Change Secret Key (Production)
Edit `app/auth.py`:
```python
SECRET_KEY = "your-very-strong-random-secret-key-min-32-chars"  # Change this!
```

### Modify Initial Balance
Edit `app/main.py` in the register function:
```python
balance=100000.0  # Change this value
```

### Add More Stocks
Edit `app/utils/market_utils.py`:
```python
VALID_SYMBOLS = [
    'RELIANCE', 'INFY', 'TCS', 'WIPRO', 'HDFC', 'HDFCBANK',
    # Add more symbols here
]
```

---

## 🛠️ Testing with Postman/cURL

### 1. Register User
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "Test@123"
  }' | jq
```

Save the `access_token` from response.

### 2. Buy a Stock
```bash
curl -X POST http://localhost:8000/api/trading/buy \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "RELIANCE",
    "quantity": 5,
    "price": 2850
  }' | jq
```

### 3. Check Portfolio
```bash
curl -X GET http://localhost:8000/api/portfolio/balance \
  -H "Authorization: Bearer YOUR_TOKEN" | jq
```

### 4. Get Trading Signals
```bash
curl -X POST http://localhost:8000/api/trading/signals/INFY | jq
```

---

## 📊 Database Schema

### Users Table
- `id` (Primary Key)
- `username` (Unique)
- `password_hash`
- `email` (Unique)
- `balance` (Default: 100000)
- `created_at`
- `is_active`

### Holdings Table
- `id` (Primary Key)
- `user_id` (Foreign Key)
- `symbol`
- `quantity`
- `average_price`
- `current_price`
- `created_at`
- `updated_at`

### Trades Table
- `id` (Primary Key)
- `user_id` (Foreign Key)
- `symbol`
- `trade_type` (BUY/SELL)
- `quantity`
- `price`
- `total_value`
- `entry_price`
- `stop_loss`
- `target`
- `status` (OPEN/CLOSED)
- `created_at`
- `closed_at`

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Change port in run.py
uvicorn.run(..., port=8001)

# Or kill the process using port 8000
# Windows: netstat -ano | findstr :8000
# Mac/Linux: lsof -i :8000
```

### Module Not Found Errors
```bash
# Ensure virtual environment is activated
# Reinstall dependencies
pip install -r requirements.txt
```

### yFinance Rate Limiting
If getting rate limit errors, add delay:
```python
import time
time.sleep(2)  # Wait 2 seconds between requests
```

---

## 📚 Frontend Integration

Connect frontend to this backend by updating the API endpoint:

```javascript
// In your frontend JavaScript
const API_URL = "http://localhost:8000";

// Example: Login
fetch(`${API_URL}/api/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'trader123',
    password: 'password123'
  })
})
.then(r => r.json())
.then(data => {
  localStorage.setItem('token', data.access_token);
});
```

---

## ✅ Next Steps

1. ✅ Backend running locally
2. ⏳ Integrate with frontend (update API endpoints)
3. ⏳ Deploy to production (use gunicorn, nginx)
4. ⏳ Add more advanced features (alerts, notifications, ML models)
5. ⏳ Implement WebSockets for real-time updates

---

## 📞 Support

If you encounter issues:
1. Check the API docs at http://localhost:8000/docs
2. Review error messages in console
3. Ensure all dependencies are installed
4. Verify token is included in Authorization header