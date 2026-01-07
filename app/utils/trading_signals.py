# app/utils/trading_signals.py

import numpy as np
from typing import Dict
from datetime import datetime

class TradingSignalGenerator:
    """Generate multi-horizon trading signals"""
    
    @staticmethod
    def generate_signals(symbol: str, current_price: float, historical_data: list) -> Dict:
        """Generate signals for all three horizons"""
        
        # Extract close prices from historical data
        closes = [d['close'] for d in historical_data[-100:]]  # Last 100 days
        
        # Calculate technical indicators
        sma_20 = TradingSignalGenerator._calculate_sma(closes, 20)
        sma_50 = TradingSignalGenerator._calculate_sma(closes, 50)
        rsi = TradingSignalGenerator._calculate_rsi(closes, 14)
        
        # Intraday signals (1-24 hours)
        intraday = TradingSignalGenerator._generate_intraday_signal(
            current_price, closes, rsi, sma_20
        )
        
        # Short-term signals (1-4 weeks)
        shortterm = TradingSignalGenerator._generate_shortterm_signal(
            current_price, closes, sma_20, sma_50
        )
        
        # Long-term signals (months-years)
        longterm = TradingSignalGenerator._generate_longterm_signal(
            current_price, closes, sma_50
        )
        
        # Consolidated signal
        consolidated = TradingSignalGenerator._consolidate_signals(
            intraday, shortterm, longterm, current_price
        )
        
        return {
            "symbol": symbol,
            "current_price": current_price,
            "intraday": intraday,
            "shortterm": shortterm,
            "longterm": longterm,
            "consolidated": consolidated,
            "timestamp": datetime.now()
        }
    
    @staticmethod
    def _calculate_sma(prices: list, period: int) -> float:
        """Simple Moving Average"""
        if len(prices) < period:
            return prices[-1] if prices else 0
        return sum(prices[-period:]) / period
    
    @staticmethod
    def _calculate_rsi(prices: list, period: int = 14) -> float:
        """Relative Strength Index"""
        if len(prices) < period:
            return 50
        
        deltas = np.diff(prices[-period-1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        
        if avg_loss == 0:
            return 100 if avg_gain > 0 else 50
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi)
    
    @staticmethod
    def _generate_intraday_signal(price: float, closes: list, rsi: float, sma_20: float) -> Dict:
        """Generate intraday signal (0-24 hours) - High frequency"""
        current_close = closes[-1] if closes else price
        
        # RSI-based signal (overbought/oversold)
        if rsi < 30:
            signal = "BUY"
            entry = price * 0.995
            stop_loss = price * 0.97
            target = price * 1.02
            confidence = 75
        elif rsi > 70:
            signal = "SELL"
            entry = price * 1.005
            stop_loss = price * 1.03
            target = price * 0.98
            confidence = 75
        else:
            signal = "NEUTRAL"
            entry = price
            stop_loss = price * 0.98
            target = price * 1.01
            confidence = 60
        
        risk_reward = (target - entry) / (entry - stop_loss) if entry != stop_loss else 1.0
        
        return {
            "signal": signal,
            "entry": round(entry, 2),
            "stop_loss": round(stop_loss, 2),
            "target": round(target, 2),
            "confidence": confidence,
            "risk_reward": round(risk_reward, 2)
        }
    
    @staticmethod
    def _generate_shortterm_signal(price: float, closes: list, sma_20: float, sma_50: float) -> Dict:
        """Generate short-term signal (1-4 weeks) - Medium frequency"""
        current_close = closes[-1] if closes else price
        
        # Moving average crossover
        if sma_20 > sma_50 and current_close > sma_20:
            signal = "BUY"
            entry = price * 0.99
            stop_loss = price * 0.95
            target = price * 1.05
            confidence = 82
        elif sma_20 < sma_50 and current_close < sma_20:
            signal = "SELL"
            entry = price * 1.01
            stop_loss = price * 1.05
            target = price * 0.95
            confidence = 82
        else:
            signal = "NEUTRAL"
            entry = price
            stop_loss = price * 0.96
            target = price * 1.04
            confidence = 65
        
        risk_reward = (target - entry) / (entry - stop_loss) if entry != stop_loss else 1.5
        
        return {
            "signal": signal,
            "entry": round(entry, 2),
            "stop_loss": round(stop_loss, 2),
            "target": round(target, 2),
            "confidence": confidence,
            "risk_reward": round(risk_reward, 2)
        }
    
    @staticmethod
    def _generate_longterm_signal(price: float, closes: list, sma_50: float) -> Dict:
        """Generate long-term signal (months-years) - Low frequency"""
        current_close = closes[-1] if closes else price
        
        # Trend-based signal
        trend = (current_close - closes[0]) / closes[0] * 100 if closes else 0
        
        if sma_50 > closes[-20:] and trend > 2:  # Uptrend
            signal = "BUY"
            entry = price
            stop_loss = price * 0.92
            target = price * 1.15
            confidence = 80
        elif sma_50 < closes[-20:] and trend < -2:  # Downtrend
            signal = "SELL"
            entry = price
            stop_loss = price * 1.08
            target = price * 0.85
            confidence = 80
        else:
            signal = "NEUTRAL"
            entry = price
            stop_loss = price * 0.90
            target = price * 1.20
            confidence = 70
        
        risk_reward = (target - entry) / (entry - stop_loss) if entry != stop_loss else 2.0
        
        return {
            "signal": signal,
            "entry": round(entry, 2),
            "stop_loss": round(stop_loss, 2),
            "target": round(target, 2),
            "confidence": confidence,
            "risk_reward": round(risk_reward, 2)
        }
    
    @staticmethod
    def _consolidate_signals(intraday: Dict, shortterm: Dict, longterm: Dict, price: float) -> Dict:
        """Consolidate signals, resolving conflicts"""
        
        # Weight confidence scores
        weights = {
            "intraday": 0.3,    # Least important
            "shortterm": 0.4,   # Most important
            "longterm": 0.3     # Medium importance
        }
        
        # Determine consolidated signal
        signals = [intraday["signal"], shortterm["signal"], longterm["signal"]]
        
        # Majority vote
        buy_count = signals.count("BUY")
        sell_count = signals.count("SELL")
        
        if buy_count > 1:
            consolidated_signal = "BUY"
        elif sell_count > 1:
            consolidated_signal = "SELL"
        else:
            consolidated_signal = shortterm["signal"]  # Default to short-term
        
        # Weighted average confidence
        avg_confidence = int(
            intraday["confidence"] * weights["intraday"] +
            shortterm["confidence"] * weights["shortterm"] +
            longterm["confidence"] * weights["longterm"]
        )
        
        # Blended entry/SL/target (weighted by confidence)
        total_conf = intraday["confidence"] + shortterm["confidence"] + longterm["confidence"]
        
        entry = (
            intraday["entry"] * (intraday["confidence"] / total_conf) +
            shortterm["entry"] * (shortterm["confidence"] / total_conf) +
            longterm["entry"] * (longterm["confidence"] / total_conf)
        )
        
        stop_loss = (
            intraday["stop_loss"] * (intraday["confidence"] / total_conf) +
            shortterm["stop_loss"] * (shortterm["confidence"] / total_conf) +
            longterm["stop_loss"] * (longterm["confidence"] / total_conf)
        )
        
        target = (
            intraday["target"] * (intraday["confidence"] / total_conf) +
            shortterm["target"] * (shortterm["confidence"] / total_conf) +
            longterm["target"] * (longterm["confidence"] / total_conf)
        )
        
        risk_reward = (target - entry) / (entry - stop_loss) if entry != stop_loss else 2.0
        
        return {
            "signal": consolidated_signal,
            "entry": round(entry, 2),
            "stop_loss": round(stop_loss, 2),
            "target": round(target, 2),
            "confidence": avg_confidence,
            "risk_reward": round(risk_reward, 2),
            "conflict_resolution": "Short-term signal weighted as primary"
        }