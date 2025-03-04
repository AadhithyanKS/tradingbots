import pandas as pd
import numpy as np
import yfinance as yf
import time
from plyer import notification
import pandas_ta as ta
import traceback


import requests

TELEGRAM_BOT_TOKEN = "7567349886:AAGkdY0J4y6eNGD8NPvjs_vczWwXVgLJ3-A"
TELEGRAM_CHAT_ID = "497272030"


def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    params = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    response = requests.get(url, params=params)
    return response.json()

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
        df = yf.download(stock, interval="5m", period="3d", progress=False)
        df.dropna(inplace=True)

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)

        # Calculate EMAs
        df["EMA_5"] = df["Close"].ewm(span=5, adjust=False).mean()
        df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()
        df["EMA_21"] = df["Close"].ewm(span=21, adjust=False).mean()

        #MACD
        macd_df = ta.macd(df["Close"], fast=12, slow=26, signal=9)   
        #print(macd_df)   
        # Assign correct column names
        df["MACD"] = macd_df["MACD_12_26_9"]
        df["MACD_Signal"] = macd_df["MACDs_12_26_9"] 

        # Get latest & previous row (Fix for Series Issue)
        latest = df.iloc[-1].copy()  # Ensure it's a proper Series
        previous = df.iloc[-2].copy()

        # Extract scalar values (Fix for ambiguous Series issue)
        EMA_5_latest = latest["EMA_5"].item()
        EMA_20_latest = latest["EMA_20"].item()
        ema_21_latest = latest["EMA_21"].item()
        EMA_5_previous = previous["EMA_5"].item()
        EMA_20_previous = previous["EMA_20"].item()
        macdlatest = latest["MACD"].item()
        macdSignallatest = latest["MACD_Signal"].item()
        #print(macdlatest)
        #print(macdSignallatest)

        

        # Buy/Sell Conditions (Fix applied)
        buy_signal = (EMA_5_latest > EMA_20_latest) and (EMA_5_previous <= EMA_20_previous) and macdlatest>macdSignallatest and macdlatest>0
        sell_signal = (EMA_5_latest < EMA_20_latest) and (EMA_5_previous >= EMA_20_previous) and macdlatest<macdSignallatest and macdlatest<0

        # Send notifications only if there's a new signal
        current_time = time.strftime("%H:%M:%S")
        if buy_signal and last_signals.get(stock) != "BUY":
            notification.notify(title="BUY Signal", message=f"{stock}: Buy at {latest['Close']} ({current_time})", timeout=5)
            print(f"\n🔼 BUY: {stock} at {latest['Close']} ({current_time})")
            send_telegram_message(f"\n🔼 BUY: {stock} at {latest['Close']} ({current_time})")
            last_signals[stock] = "BUY"
            print(f"\n{stock} - Latest EMA Values:")
            print(f"EMA_5: {EMA_5_latest}, EMA_20: {EMA_20_latest}, EMA_21: {ema_21_latest}")


        elif sell_signal and last_signals.get(stock) != "SELL":
            notification.notify(title="SELL Signal", message=f"{stock}: Sell at {latest['Close']} ({current_time})", timeout=5)
            print(f"\n🔻 SELL: {stock} at {latest['Close']} ({current_time})")
            send_telegram_message(f"\n🔻 SELL: {stock} at {latest['Close']} ({current_time})")
            last_signals[stock] = "SELL"
            print(f"\n{stock} - Latest EMA Values:")
            print(f"EMA_5: {EMA_5_latest}, EMA_20: {EMA_20_latest}, EMA_21: {ema_21_latest}")

    except Exception as e:
        print(f"Error fetching {stock}: {e}")
        print(traceback.format_exc())

# Run the Strategy Continuously
while True:
    print(f"\nChecking signals at {time.strftime('%H:%M:%S')}...\n")
    for stock in nifty50_tickers:
        check_signals(stock)
    print("\nSleeping for 60 seconds...\n")
    time.sleep(150)  # Check every minute
