import pandas as pd
import yfinance as yf
import pandas_ta as ta
import pytz

ist = pytz.timezone("Asia/Kolkata")

# Fetch historical stock data
stock = "KALYANKJIL.NS"  # Change as needed
df = yf.download(stock, interval="5m", period="3d", progress=False)
df.dropna(inplace=True)

if isinstance(df.columns, pd.MultiIndex):
   df.columns = df.columns.droplevel(1)

print(df)

# Convert timezone
df.index = df.index.tz_convert(ist)

# Calculate Indicators
df["EMA_5"] = df["Close"].ewm(span=5, adjust=False).mean()
df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()
df["RSI"] = ta.rsi(df["Close"],length=14)

#MACD
macd_df = ta.macd(df["Close"], fast=12, slow=26, signal=9)
    
# Assign correct column names
df["MACD"] = macd_df["MACD_12_26_9"]
df["MACD_Signal"] = macd_df["MACDs_12_26_9"]    

#df["RSI"] = df["RSI"].fillna(0) 

df.to_csv("Data.csv", index=False)

# Backtest Variables
initial_balance = 10000  # Starting capital
balance = initial_balance
trade_log = []
wins = 0
losses = 0
position = None  # None = no trade, "BUY" = in a long trade
entry_price = 0


win = 0
loss = 0

# Simulate Trades
for i in range(4, len(df)):

    # Extract values
    EMA_5_latest = df["EMA_5"].iloc[i]
    EMA_20_latest = df["EMA_20"].iloc[i]
    EMA_5_previous = df["EMA_5"].iloc[i - 1]
    EMA_20_previous = df["EMA_20"].iloc[i - 1]
    EMA_5_previous2 = df["EMA_5"].iloc[i - 2]
    EMA_20_previous2 = df["EMA_20"].iloc[i - 2]
    RSI_latest = df["RSI"].iloc[i]
    macdlatest = df["MACD"].iloc[i].item()
    macdSignallatest = df["MACD_Signal"].iloc[i].item()
    close_price = df["Close"].iloc[i]
    timestamp = df.index[i]
    qty = 150
    # Buy Signal
    
    
    if (EMA_5_latest > EMA_20_latest) and ((EMA_5_previous<EMA_20_previous) or (EMA_5_previous2<EMA_20_previous2)) and macdlatest>macdSignallatest and macdlatest>0 and timestamp.time() <= pd.to_datetime("14:00:00").time() and position is None:

        position = "BUY"
        
        entry_price = close_price
        trade_log.append(f"Long at {entry_price} , Time: {timestamp}") #  {EMA_5_latest}, {EMA_20_latest}, {EMA_5_previous},  {EMA_20_previous}
        
    elif EMA_5_latest < EMA_20_latest and ((EMA_5_previous>EMA_20_previous) or (EMA_5_previous2>EMA_20_previous2)) and macdlatest<macdSignallatest and macdlatest<0 and timestamp.time() <= pd.to_datetime("14:00:00").time() and position is None:
        position = "SELL"
         
        entry_price = close_price
        trade_log.append(f"Short at {entry_price} , Time: {timestamp}")

    # Sell Signal (Exit Trade)

    elif close_price > entry_price + (entry_price/100) and position == "BUY":
        position = None
        exit_price = close_price
        win+=1
        profit = (exit_price - entry_price) * qty
        balance += profit  # Adjust balance
        trade_log.append(f"Exit Long at {exit_price}, Time: {timestamp}, Profit: {profit}")

    elif close_price < entry_price - (entry_price/100) and position == "SELL":
        position = None
        exit_price = close_price
        win+=1
        profit = -(exit_price - entry_price) * qty
        balance += profit  # Adjust balance
        trade_log.append(f"Exit Short at {exit_price}, Time: {timestamp}, Profit: {profit}")
    
    #Stoploss
    elif close_price < entry_price - (entry_price/100) and position == "BUY":
        position = None
        loss+=1
        exit_price = entry_price - (entry_price/100)
        profit = (exit_price - entry_price) * qty
        balance += profit  # Adjust balance
        trade_log.append(f"Stoploss at {exit_price}, Time: {timestamp}, Loss: {profit}")
                    
    elif close_price > entry_price + (entry_price/100) and position == "SELL":
        position = None
        loss+=1
        exit_price = entry_price + (entry_price/100)
        profit = (exit_price - entry_price) * qty
        balance += profit  # Adjust balance
        trade_log.append(f"Stoploss at {exit_price}, Time: {timestamp}, Loss: {profit}")

    elif timestamp.time() >= pd.to_datetime("15:00:00").time() and position is not None:
        position = None
        exit_price = close_price
        loss+=1
        profit = 0
        balance += profit  # Adjust balance
        trade_log.append(f"Squared off at {exit_price}, Time: {timestamp}, Loss/Profit: {profit}")


# Calculate Win %
total_trades = win + loss
win_percentage = (win / total_trades * 100) if total_trades > 0 else 0

# Print Results
print("\n📊 Backtest Results:")
print(f"Initial Balance: ₹{initial_balance}")
print(f"Final Balance: ₹{balance}")
print(f"Total Trades: {total_trades}")
print(f"Wins: {win}, Losses: {loss}")
print(f"Win %: {win_percentage:.2f}%")
print("\nTrade Log:")
print("\n".join(trade_log))
