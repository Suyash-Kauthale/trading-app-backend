# ai_agent.py

import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib
from typing import Dict


class AdvancedTradingAI:
    def __init__(self, ticker: str):
        self.ticker = ticker.upper()
        self.model = RandomForestClassifier(
            n_estimators=200,
            min_samples_split=10,
            random_state=42
        )
        self.data = None
        self.interval = "1d"  # default daily

    # ---------- DATA + MODEL ----------

    def fetch_data(self, mode: str = "long"):
        """
        modes:
        - 'intraday' -> 5m, ~5d history
        - 'long'     -> 1d, 2y history
        """
        if mode == "intraday":
            self.interval = "5m"
            period = "5d"
        else:
            self.interval = "1d"
            period = "2y"

        print(f"Fetching {self.interval} data for {self.ticker}...")
        df = yf.Ticker(self.ticker).history(period=period, interval=self.interval)
        if len(df) < 50:
            raise ValueError(f"Not enough data for {self.ticker} (Mode: {mode})")
        self.data = df

    def add_indicators(self) -> pd.DataFrame:
        df = self.data.copy()

        # 1. Log returns
        df["Log_Return"] = np.log(df["Close"] / df["Close"].shift(1))

        # 2. SMA
        df["SMA_10"] = df["Close"].rolling(window=10).mean()

        # 3. RSI
        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))

        # 4. Volatility
        df["Volatility"] = df["Log_Return"].rolling(window=10).std()

        # 5. Target
        df["Target"] = (df["Close"].shift(-1) > df["Close"]).astype(int)

        self.data = df.dropna()
        return self.data

    def train(self):
        features = ["Log_Return", "SMA_10", "RSI", "Volatility", "Volume"]
        X = self.data[features]
        y = self.data["Target"]
        self.model.fit(X, y)
        return self.model

    def predict_raw(self) -> Dict:
        """
        Raw prediction: direction + confidence + latest features.
        """
        features = ["Log_Return", "SMA_10", "RSI", "Volatility", "Volume"]
        latest_row = self.data.iloc[-1]
        X_latest = latest_row[features].to_frame().T

        pred_label = int(self.model.predict(X_latest)[0])
        proba_up = float(self.model.predict_proba(X_latest)[0][1])

        direction = "UP" if pred_label == 1 else "DOWN"
        current_price = float(latest_row["Close"])

        return {
            "symbol": self.ticker,
            "direction": direction,
            "confidence": proba_up,
            "current_price": current_price,
            "rsi": float(latest_row["RSI"]),
            "sma_10": float(latest_row["SMA_10"]),
            "volatility": float(latest_row["Volatility"]),
        }

    def save_brain(self, filename="model.pkl"):
        joblib.dump(self.model, filename)

    def load_brain(self, filename="model.pkl"):
        self.model = joblib.load(filename)

    # ---------- EXPLANATION + STRATEGY LAYER ----------

    def explain_why(self, pred: Dict) -> str:
        """
        Simple human explanation using RSI, SMA and volatility.
        """
        parts = []

        if pred["direction"] == "UP":
            parts.append(f"The model expects {pred['symbol']} to move up.")
        else:
            parts.append(f"The model expects {pred['symbol']} to be weak or move down.")

        parts.append(
            f"Confidence is about {pred['confidence'] * 100:.0f}% based on recent pattern in price, "
            "volume, and volatility."
        )

        # RSI interpretation
        if pred["rsi"] < 30:
            parts.append("RSI is in oversold zone (<30), which often supports a bounce.")
        elif pred["rsi"] > 70:
            parts.append("RSI is in overbought zone (>70), which often warns of a pullback.")
        else:
            parts.append("RSI is in a neutral range, so momentum is not extreme.")

        # SMA vs price
        if pred["current_price"] > pred["sma_10"]:
            parts.append("Price is above the 10-day moving average, showing short-term strength.")
        else:
            parts.append("Price is below the 10-day moving average, showing short-term weakness.")

        return " ".join(parts)

    def suggest_position_size(
        self,
        pred: Dict,
        account_balance: float,
        max_risk_pct: float = 1.0,
        stop_loss_pct: float = 2.0,
    ) -> Dict:
        """
        Simple percent-risk position sizing.
        """
        current_price = pred["current_price"]
        risk_cap = account_balance * (max_risk_pct / 100.0)
        per_share_risk = current_price * (stop_loss_pct / 100.0)

        if per_share_risk <= 0:
            quantity = 0
        else:
            quantity = int(risk_cap // per_share_risk)

        return {
            "suggested_quantity": quantity,
            "current_price": current_price,
            "max_risk_rupees": round(risk_cap, 2),
            "stop_loss_pct": stop_loss_pct,
        }

    def next_strategy(self, pred: Dict) -> str:
        """
        Simple text strategy template based on direction.
        """
        if pred["direction"] == "UP":
            return (
                "Consider a staggered buy: enter near support instead of all-in at once, "
                "place a stop-loss a few percent below recent swing low, and plan partial profit "
                "booking if price rallies quickly. Avoid over-leveraging."
            )
        else:
            return (
                "Be cautious with fresh longs. If already holding, tighten stop-loss or reduce exposure. "
                "Wait for signs of reversal (RSI recovery, price back above moving average) "
                "before adding new positions."
            )

    def answer(self, question: str, account_balance: float = 100000.0) -> Dict:
        """
        Main method: runs prediction and returns a natural-language answer
        depending on the question (why, how many, next strategy, etc.).
        """
        q = question.lower()
        pred = self.predict_raw()

        if "why" in q:
            answer_text = self.explain_why(pred)
        elif "how many" in q or "quantity" in q or "how much" in q:
            pos = self.suggest_position_size(pred, account_balance)
            answer_text = (
                f"If you risk about {pos['max_risk_rupees']} (≈{max(1.0, account_balance*0.01):.0f} of your account) "
                f"with a stop-loss of {pos['stop_loss_pct']}%, then a reasonable size is around "
                f"{pos['suggested_quantity']} shares near ₹{pos['current_price']:.2f}."
            )
        elif "next" in q or "strategy" in q or "plan" in q:
            answer_text = self.next_strategy(pred)
        else:
            # generic short summary
            direction_word = "rise" if pred["direction"] == "UP" else "fall"
            answer_text = (
                f"For {pred['symbol']}, the model currently expects a {direction_word} "
                f"with about {pred['confidence'] * 100:.0f}% confidence at price near "
                f"₹{pred['current_price']:.2f}."
            )

        return {
            "symbol": self.ticker,
            "prediction": pred,
            "answer": answer_text,
        }
