import pandas as pd
import numpy as np
import yfinance as yf
import time
from plyer import notification

# Fetch NIFTY 50 stock list
url = "https://archives.nseindia.com/content/indices/ind_nifty50list.csv"
df = pd.read_csv(url)
nifty50_tickers = [symbol + ".NS" for symbol in df["Symbol"]]
print(f"Tracking {len(nifty50_tickers)} stocks...")

# Store last notified signals to prevent duplicate alerts
last_signals = {}

# Function to Fetch Live Data & Generate Signals
def check_signals(stock):
    try:
        df = yf.download(stock, interval="5m", period="1d", progress=False)
        df.dropna(inplace=True)

        # Calculate EMAs
        df["EMA_8"] = df["Close"].ewm(span=8, adjust=False).mean()
        df["EMA_13"] = df["Close"].ewm(span=13, adjust=False).mean()
        df["EMA_21"] = df["Close"].ewm(span=21, adjust=False).mean()

        # Get latest & previous row (Fix for Series Issue)
        latest = df.iloc[-1].copy()  # Ensure it's a proper Series
        previous = df.iloc[-2].copy()

        # Extract scalar values (Fix for ambiguous Series issue)
        ema_8_latest = latest["EMA_8"].item()
        ema_13_latest = latest["EMA_13"].item()
        ema_21_latest = latest["EMA_21"].item()
        ema_8_previous = previous["EMA_8"].item()
        ema_13_previous = previous["EMA_13"].item()

        

        # Buy/Sell Conditions (Fix applied)
        buy_signal = (ema_8_latest > ema_13_latest > ema_21_latest) and (ema_8_previous <= ema_13_previous)
        sell_signal = (ema_8_latest < ema_13_latest < ema_21_latest) and (ema_8_previous >= ema_13_previous)

        # Send notifications only if there's a new signal
        current_time = time.strftime("%H:%M:%S")
        if buy_signal and last_signals.get(stock) != "BUY":
            notification.notify(title="BUY Signal", message=f"{stock}: Buy at {latest['Close']} ({current_time})", timeout=5)
            print(f"\n🔼 BUY: {stock} at {latest['Close']} ({current_time})")
            last_signals[stock] = "BUY"
            print(f"\n{stock} - Latest EMA Values:")
            print(f"EMA_8: {ema_8_latest}, EMA_13: {ema_13_latest}, EMA_21: {ema_21_latest}")


        elif sell_signal and last_signals.get(stock) != "SELL":
            notification.notify(title="SELL Signal", message=f"{stock}: Sell at {latest['Close']} ({current_time})", timeout=5)
            print(f"\n🔻 SELL: {stock} at {latest['Close']} ({current_time})")
            last_signals[stock] = "SELL"
            print(f"\n{stock} - Latest EMA Values:")
            print(f"EMA_8: {ema_8_latest}, EMA_13: {ema_13_latest}, EMA_21: {ema_21_latest}")

    except Exception as e:
        print(f"Error fetching {stock}: {e}")

# Run the Strategy Continuously
while True:
    print(f"\nChecking signals at {time.strftime('%H:%M:%S')}...\n")
    for stock in nifty50_tickers:
        check_signals(stock)
    print("\nSleeping for 60 seconds...\n")
    time.sleep(150)  # Check every minute
