import pandas as pd
import yfinance as yf
import pandas_ta as ta
import matplotlib.pyplot as plt
import os
import numpy as np

# Fetch historical data
symbol = "KALYANKJIL.NS"  # Change as needed
df = yf.download(symbol, period="5d", interval="5m")

print(df)

df.index = df.index.tz_convert("Asia/Kolkata")
df.index = pd.to_datetime(df.index).tz_localize(None)

if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.droplevel(1)

print(df)

# Ensure correct column names
df.columns = df.columns.str.lower()

# Calculate Moving Averages
df["EMA_8"] = df["close"].ewm(span=8, adjust=False).mean()  # 10-period SMA
#df["SMA_20"] = df["close"].rolling(window=20).mean()  # 50-period SMA
df["EMA_13"] = df["close"].ewm(span=13, adjust=False).mean()  # 10-period EMA
df["EMA_21"] = df["close"].ewm(span=21, adjust=False).mean()  # 50-period EMA

#supertrend = ta.supertrend(df["high"], df["low"], df["close"], length=10, multiplier=3)
#df["Supertrend"] = supertrend["SUPERTd_10_3.0"]

df["VWAP"] = ta.vwap(df["high"], df["low"], df["close"], df["volume"])

df["RSI"] = ta.rsi(df["close"], length=14)
print(df.head(20))

sar = ta.psar(df["high"], df["low"], df["close"])
df["Parabolic_SAR"] = sar["PSARl_0.02_0.2"]

df["Trend_Long"] =  (df["close"] > df["VWAP"])
df["Trend_Short"] = (df["close"] < df["VWAP"])

#MACD
macd_df = ta.macd(df["close"], fast=12, slow=26, signal=9)
print(macd_df)
    
# Assign correct column names
df["MACD"] = macd_df["MACD_12_26_9"]
df["MACD_Signal"] = macd_df["MACDs_12_26_9"]

df["Time"] = df.index.time
df = df[(df["Time"] >= pd.to_datetime("09:15:00").time()) & (df["Time"] <= pd.to_datetime("15:30:00").time())]

# Define Buy/Sell signals

# Initialize buy and sell signals
df["Buy_Signal"] = False
df["Sell_Signal"] = False

df["EMA Crossed for sell"] = (df["EMA_8"] < df["EMA_13"]) & (df["EMA_8"] < df["EMA_21"])
df["EMA Crossed for buy"] = (df["EMA_8"] > df["EMA_13"]) & (df["EMA_8"] > df["EMA_21"])

# Identify crossover points
df["Buy_Signal"] = (df["EMA Crossed for buy"] & ((df["EMA_8"].shift(1) <= df["EMA_13"].shift(1)) | (df["EMA_8"].shift(1) <= df["EMA_21"].shift(1)))) | df["EMA Crossed for buy"] & ((df["EMA_8"].shift(2) <= df["EMA_13"].shift(2)) | (df["EMA_8"].shift(2) <= df["EMA_21"].shift(2)))
df["Sell_Signal"] = (df["EMA Crossed for sell"] & ((df["EMA_8"].shift(1) >= df["EMA_13"].shift(1)) | (df["EMA_8"].shift(1) >= df["EMA_21"].shift(1)))) | df["EMA Crossed for sell"] & ((df["EMA_8"].shift(2) >= df["EMA_13"].shift(2)) | (df["EMA_8"].shift(2) >= df["EMA_21"].shift(2)))

#df["Buy"] = df.apply(buy_signal, axis=1)
#df["Sell"] = df.apply(sell_signal, axis=1)



df["MACD Indication"] = np.where(df["MACD"] > df["MACD_Signal"], "Buy", "Sell")

# Confirm Buy only if MACD
df["Buy_Confirmed"] = df["Buy_Signal"] & (df["MACD"] > df["MACD_Signal"]) & (df["RSI"] > 50) & (df["Supertrend"] == 1)

# Confirm Sell only if MACD
df["Sell_Confirmed"] = df["Sell_Signal"] & (df["MACD"] < df["MACD_Signal"]) & (df["RSI"] < 50) & (df["Supertrend"] == -1)



#BACKTEstiNG

# Square-off all trades before market close (3:30 PM)
df["Square_Off"] = df["Time"] >= pd.to_datetime("15:29:00").time()

# Backtesting: Calculate profit/loss per trade with risk-reward ratio
risk_reward_ratio = 1.5  # Example: Setting reward as 2x risk
stop_loss = 0.005  # Example: 0.5% stop-loss

# Backtesting: Track entry, stop loss, target, and profit calculation
entries = []
exit_prices = []
profits = []
trade_open = False
entry_price = 0
stop_loss = 0
target_price = 0

for index, row in df.iterrows():
    if row["Buy_Confirmed"] and not trade_open:
        entry_price = row["close"]
        stop_loss = entry_price * (1 - stop_loss)
        target_price = entry_price * (1 + risk_reward_ratio * stop_loss)
        trade_open = True
        entries.append(entry_price)
        exit_prices.append(np.nan)
        profits.append(np.nan)
    elif trade_open:
        if row["close"] >= target_price or row["close"] <= stop_loss or row["Sell_Confirmed"] or row["Square_Off"]:
            exit_price = row["close"]
            entries.append(np.nan)
            exit_prices.append(exit_price)
            profits.append(exit_price - entry_price)
            trade_open = False
        else:
            entries.append(np.nan)
            exit_prices.append(np.nan)
            profits.append(np.nan)
    else:
        entries.append(np.nan)
        exit_prices.append(np.nan)
        profits.append(np.nan)

# Add calculated values to dataframe
df["Entry_Price"] = entries
df["Exit_Price"] = exit_prices
df["Profit/Loss"] = profits


'''
# Initialize tracking columns
df["Trade_Profit"] = 0  # Store profit/loss per trade

# Track open trades
position = None
entry_price = 0
profit = 0
capital = 100000  # Starting capital
risk_per_trade = 0.02 * capital  # Risk 2% per trade

for i in range(1, len(df)):
    if df["Buy_Confirmed"].iloc[i] and position is None:
        position = "LONG"
        entry_price = df["close"].iloc[i]
        stop_loss = df["low"].iloc[i]
        target_price = entry_price + (entry_price - stop_loss) * 1.5  # 1.5 Risk-Reward Ratio

    elif df["Sell_Confirmed"].iloc[i] and position is None:
        position = "SHORT"
        entry_price = df["close"].iloc[i]
        stop_loss = df["high"].iloc[i]
        target_price = entry_price - (stop_loss - entry_price) * 1.5  # 1.5 Risk-Reward Ratio

    # Exit logic: Stop-loss, target hit, or 3:29 PM square-off
    if position:
        trade_profit = 0  # Track individual trade profit
        
        if position == "LONG":
            if df["high"].iloc[i] >= target_price:
                trade_profit = risk_per_trade * 1.5
                position = None
            elif df["low"].iloc[i] <= stop_loss:
                trade_profit = -risk_per_trade
                position = None
        elif position == "SHORT":
            if df["low"].iloc[i] <= target_price:
                trade_profit = risk_per_trade * 1.5
                position = None
            elif df["high"].iloc[i] >= stop_loss:
                trade_profit = -risk_per_trade
                position = None

        # Square-off at 3:29 PM
        if df["datetime"].iloc[i] >= pd.to_datetime("15:29:00").time():
            position = None
        
        # Store trade profit
        df.at[df.index[i], "Trade_Profit"] = trade_profit
        profit += trade_profit  # Update total profit

print(f"Total Profit: {profit}")

# Show the last few trades for analysis
print(df[["Close", "Buy_Confirmed", "Sell_Confirmed", "Trade_Profit"]].tail(20))
'''


df.to_csv(r"C:\Users\Aadhithyan\Desktop\codes\Trading code\Output.csv")

#fd = os.open(r"C:\Users\Aadhithyan\Desktop\codes\Trading code\Output.csv")




'''
Chart printing
plt.figure(figsize=(12, 6))
plt.plot(df.index, df["close"], label="Close Price", color="blue")
plt.plot(df.index, df["SMA_5"], label="SMA 5", color="green", linestyle="--")
plt.plot(df.index, df["SMA_20"], label="SMA 20", color="red", linestyle="--")

# Mark Buy/Sell signals
plt.scatter(df.index[df["Buy_Signal"]], df["close"][df["Buy_Signal"]], label="Buy Signal", marker="^", color="green", alpha=1)
plt.scatter(df.index[df["Sell_Signal"]], df["close"][df["Sell_Signal"]], label="Sell Signal", marker="v", color="red", alpha=1)

plt.title(f"Moving Average Crossover Strategy for {symbol}")
plt.legend()
plt.show()
'''
