# ENHANCED FRONTEND - LOGIN & REGISTRATION GUIDE

## Features Added to Your Dashboard:

### 1. **Authentication Pages**
   - Register: Create account with username, email, password
   - Login: Sign in with credentials
   - JWT Token Management (stored in browser)

### 2. **Protected Routes**
   - Dashboard accessible only when logged in
   - Token sent with every API request
   - Auto-logout on token expiry

### 3. **Trading Features**
   - Buy/Sell stocks with your ₹100,000 initial balance
   - Real-time portfolio tracking
   - P&L calculations
   - Trade history

### 4. **Market Data**
   - Real-time stock prices (yFinance)
   - Interactive charts (OHLCV data)
   - Multi-horizon trading signals
   - Stock search functionality

---

## Integration Steps:

### 1. Update API Endpoint in Dashboard
In the HTML file, update the fetch URL:

```javascript
const API_URL = "http://localhost:8000";  // Add this at top

// Update generateTradePlan() function:
async function generateTradePlan() {
    const token = localStorage.getItem('token');
    
    const response = await fetch(`${API_URL}/api/trading/signals/${symbol}`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
}
```

### 2. Add Chart Library (for real-time charts)
Add to your HTML `<head>`:

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
```

### 3. Buy/Sell Stocks
```javascript
async function buyStock() {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_URL}/api/trading/buy`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            symbol: 'RELIANCE',
            quantity: 10,
            price: 2850.50
        })
    });
}
```

---

## Frontend + Backend Flow:

```
User Opens App
    ↓
Not Logged In? → Show Login/Register
    ↓
User Registers → Backend creates account with ₹100,000
    ↓
User Logs In → Backend returns JWT token
    ↓
Store Token → localStorage.setItem('token', token)
    ↓
Access Dashboard → Send token with each API request
    ↓
View Portfolio → Fetch from /api/portfolio/balance (with token)
    ↓
Buy Stock → POST to /api/trading/buy (with token)
    ↓
Get Signals → POST to /api/trading/signals/{symbol}
    ↓
View Charts → GET /api/market/chart/{symbol}
```

---

## Key API Integration Points:

### 1. Authentication Token
```javascript
// Save after login
const token = response.data.access_token;
localStorage.setItem('token', token);

// Use in every request
headers: {
    'Authorization': `Bearer ${token}`
}

// Clear on logout
localStorage.removeItem('token');
```

### 2. Portfolio Updates
```javascript
// Get balance and holdings every 5 seconds
setInterval(async () => {
    const response = await fetch(`${API_URL}/api/portfolio/balance`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    const portfolio = await response.json();
    updatePortfolioUI(portfolio);
}, 5000);
```

### 3. Real-Time Price Updates
```javascript
// Get current price
async function updatePrices() {
    const symbols = ['RELIANCE', 'INFY', 'TCS'];
    for (const symbol of symbols) {
        const response = await fetch(
            `${API_URL}/api/market/price/${symbol}`
        );
        const data = await response.json();
        updatePrice(symbol, data.current_price);
    }
}

setInterval(updatePrices, 5000);  // Update every 5 seconds
```

### 4. Chart Data
```javascript
// Get historical data for charts
async function loadChart(symbol) {
    const response = await fetch(
        `${API_URL}/api/market/chart/${symbol}?period=1mo`
    );
    const data = await response.json();
    
    // Use Chart.js to render
    renderChart(data.data);
}
```

---

## Testing the Complete Flow:

### 1. Start Backend
```bash
cd trading-app-backend
python run.py
# Server at http://localhost:8000
```

### 2. Test with cURL (Backend Testing)
```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "trader1",
    "email": "trader@example.com",
    "password": "Pass@123"
  }' | jq '.access_token' -r > token.txt

# Use token
TOKEN=$(cat token.txt)
curl -X GET http://localhost:8000/api/portfolio/balance \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Open Frontend in Browser
- Create `index.html` with login screen
- After login, show dashboard
- Use stored token for all requests

---

## Complete Frontend Login Flow (JavaScript)

```javascript
const API_URL = "http://localhost:8000";

// LOGIN
async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    try {
        const response = await fetch(`${API_URL}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Store token
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('user_id', data.user_id);
            localStorage.setItem('username', data.username);
            
            // Redirect to dashboard
            window.location.href = '/dashboard.html';
        } else {
            alert('Login failed');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// REGISTER
async function handleRegister(event) {
    event.preventDefault();
    
    const username = document.getElementById('reg-username').value;
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;
    
    try {
        const response = await fetch(`${API_URL}/api/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });
        
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('token', data.access_token);
            alert('Registration successful! Redirecting...');
            window.location.href = '/dashboard.html';
        }
    } catch (error) {
        alert('Registration failed: ' + error.message);
    }
}

// LOGOUT
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('username');
    window.location.href = '/login.html';
}

// Check if logged in
function checkAuth() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/login.html';
    }
    return token;
}
```

---

## Database Workflow:

```
User Registration:
├─ Check if username exists
├─ Hash password (bcrypt)
├─ Create user row with ₹100,000 balance
└─ Return JWT token

User Buy Stock:
├─ Check if user has balance
├─ Deduct amount from user.balance
├─ Create/Update holding record
├─ Create trade record
└─ Return success

User Sell Stock:
├─ Check if user has holding
├─ Add amount to user.balance
├─ Update/Delete holding record
├─ Create trade record (status=CLOSED)
└─ Return success

Get Portfolio:
├─ Fetch user balance
├─ Fetch all holdings
├─ Get current price for each stock (yFinance)
├─ Calculate P&L per holding
├─ Sum portfolio value
└─ Return complete portfolio
```

---

## Next Features to Add:

1. **WebSocket Real-time Updates**
   - Live price streaming
   - Instant P&L updates
   - Real-time notifications

2. **Advanced Charts**
   - TradingView Lightweight Charts
   - Multiple timeframes (15m, 1h, 1d, 1w)
   - Technical indicators overlay

3. **Email Notifications**
   - Alert when target reached
   - Daily portfolio summary
   - Trade confirmations

4. **Mobile App**
   - React Native / Flutter
   - Same backend, different frontend
   - Push notifications

5. **Machine Learning Signals**
   - LSTM neural networks for predictions
   - Sentiment analysis from news
   - Custom ML models