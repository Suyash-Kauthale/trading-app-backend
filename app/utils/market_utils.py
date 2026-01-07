# app/utils/market_utils.py

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class MarketDataManager:
    """Manages real-time and historical market data using yFinance"""
    
    # Indian stock symbols (NSE)
    VALID_SYMBOLS = [
        'RELIANCE', 'INFY', 'TCS', 'WIPRO', 'HDFC', 'HDFCBANK',
        'ICICIBANK', 'SBIN', 'BAJAJFINSV', 'BHARTIARTL', 'ITC',
        'AXISBANK', 'MARUTI', 'ONGC', 'SUNPHARMA', 'KOTAKBANK'
    ]
    
    @staticmethod
    def get_current_price(symbol: str) -> Dict:
        """Get current price and basic info"""
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            data = ticker.history(period='1d')
            info = ticker.info
            
            if data.empty:
                return {"error": f"Symbol {symbol} not found"}
            
            current_price = data['Close'].iloc[-1]
            previous_close = info.get('previousClose', current_price)
            change = current_price - previous_close
            change_percent = (change / previous_close * 100) if previous_close > 0 else 0
            
            return {
                "symbol": symbol,
                "current_price": float(current_price),
                "previous_close": float(previous_close),
                "change": float(change),
                "change_percentage": float(change_percent),
                "timestamp": datetime.now()
            }
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def get_historical_data(symbol: str, period: str = "1mo") -> List[Dict]:
        """Get historical OHLCV data"""
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            data = ticker.history(period=period)
            
            chart_data = []
            for date, row in data.iterrows():
                chart_data.append({
                    "date": date.isoformat(),
                    "open": float(row['Open']),
                    "high": float(row['High']),
                    "low": float(row['Low']),
                    "close": float(row['Close']),
                    "volume": int(row['Volume'])
                })
            
            return chart_data
        except Exception as e:
            return []
    
    @staticmethod
    def get_intraday_data(symbol: str, interval: str = "15m") -> List[Dict]:
        """Get intraday data for real-time charts"""
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            data = ticker.history(period="1d", interval=interval)
            
            chart_data = []
            for date, row in data.iterrows():
                chart_data.append({
                    "timestamp": date.isoformat(),
                    "open": float(row['Open']),
                    "high": float(row['High']),
                    "low": float(row['Low']),
                    "close": float(row['Close']),
                    "volume": int(row['Volume'])
                })
            
            return chart_data
        except Exception as e:
            return []
    
    @staticmethod
    def get_multiple_prices(symbols: List[str]) -> Dict:
        """Get prices for multiple symbols"""
        result = {}
        for symbol in symbols:
            result[symbol] = MarketDataManager.get_current_price(symbol)
        return result
    
    @staticmethod
    def search_symbols(query: str) -> List[Dict]:
        """Search for stocks matching query"""
        matching_symbols = [
            s for s in MarketDataManager.VALID_SYMBOLS 
            if query.upper() in s
        ]
        
        results = []
        for symbol in matching_symbols[:5]:  # Return top 5
            price_data = MarketDataManager.get_current_price(symbol)
            if "error" not in price_data:
                results.append({
                    "symbol": symbol,
                    "current_price": price_data.get("current_price", 0),
                    "change_percentage": price_data.get("change_percentage", 0)
                })
        
        return results