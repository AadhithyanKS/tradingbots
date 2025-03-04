import pandas as pd
import yfinance as yf
import pandas_ta as ta
import pytz

import requests

TELEGRAM_BOT_TOKEN = "7567349886:AAGkdY0J4y6eNGD8NPvjs_vczWwXVgLJ3-A"
TELEGRAM_CHAT_ID = "497272030"


def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    params = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    response = requests.get(url, params=params)
    return response.json()

ist = pytz.timezone("Asia/Kolkata")

url = "https://archives.nseindia.com/content/indices/ind_nifty50list.csv"
df = pd.read_csv(url).head(50)
print(df)
nifty50_tickers = [symbol + ".NS" for symbol in df["Symbol"]]
print(f"Tracking {len(nifty50_tickers)} stocks...")
i = 0

global win
global loss
global totalProfit
global Finalbalance
global capital

win = 0
loss = 0

#df["RSI"] = df["RSI"].fillna(0) 
#df.to_csv("Data.csv", index=False)

def check_trades(stock):
    try:
        win = 0
        loss = 0
        balance = 0
        # Fetch historical stock data
        #stock = "KALYANKJIL.NS"  # Change as needed
        df = yf.download(stock, interval="5m", period="1d", progress=False, auto_adjust=True)
        df.dropna(inplace=True)

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)

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

        position = None
          # Starting capital
        balance = 0
        entry_price = 0
        


        # Simulate Trades
        for i in range(0, len(df)):

            # Extract values
            EMA_5_latest = df["EMA_5"].iloc[i]
            EMA_20_latest = df["EMA_20"].iloc[i]
            EMA_5_previous = df["EMA_5"].iloc[i - 1]
            EMA_20_previous = df["EMA_20"].iloc[i - 1]
            EMA_5_previous2 = df["EMA_5"].iloc[i - 2]
            EMA_20_previous2 = df["EMA_20"].iloc[i - 2]
            RSI_latest = df["RSI"].iloc[i]
            macdlatest = df["MACD"].iloc[i]
            macdSignallatest = df["MACD_Signal"].iloc[i]
            close_price = df["Close"].iloc[i]
            timestamp = df.index[i]
            qty = (capital/close_price) * 5
            
            # Buy Signal
            #print(f"{EMA_5_latest} > {EMA_20_latest}")
    
            if (EMA_5_latest > EMA_20_latest) and ((EMA_5_previous<EMA_20_previous) or (EMA_5_previous2<EMA_20_previous2)) and macdlatest>macdSignallatest and macdlatest>0 and RSI_latest>50 and timestamp.time() <= pd.to_datetime("14:00:00").time() and position is None:
            
                position = "BUY"
                entry_price = close_price
                trade_log.append(f"Long at {entry_price} , Time: {timestamp}") #  {EMA_5_latest}, {EMA_20_latest}, {EMA_5_previous},  {EMA_20_previous}

            elif EMA_5_latest < EMA_20_latest and ((EMA_5_previous>EMA_20_previous) or (EMA_5_previous2>EMA_20_previous2)) and macdlatest<macdSignallatest and macdlatest<0 and RSI_latest>50 and timestamp.time() <= pd.to_datetime("14:00:00").time() and position is None:
                position = "SELL"
                entry_price = close_price
                trade_log.append(f"Short at {entry_price} , Time: {timestamp}")

                    # Sell Signal (Exit Trade)

            elif close_price > entry_price + (entry_price/200) and position == "BUY":
                position = None
                exit_price = close_price
                win+=1
                profit = (exit_price - entry_price) * qty
                balance += profit  # Adjust balance
                trade_log.append(f"Exit Long at {exit_price}, {entry_price} Time: {timestamp}, Profit: {profit}")

            elif close_price < entry_price - (entry_price/200) and position == "SELL":
                position = None
                exit_price = close_price
                win+=1
                profit = -(exit_price - entry_price) * qty
                balance += profit  # Adjust balance
                trade_log.append(f"Exit Short at {exit_price}, Time: {timestamp}, Profit: {profit}")
            #Stoploss
            elif close_price < entry_price - (entry_price/200) and position == "BUY":
                position = None
                loss+=1
                exit_price = entry_price - (entry_price/100)
                profit = (exit_price - entry_price) * qty
                balance += profit  # Adjust balance
                trade_log.append(f"Stoploss long at {exit_price}, Time: {timestamp}, Loss: {profit}")

            elif close_price > entry_price + (entry_price/200) and position == "SELL":
                position = None
                loss+=1
                exit_price = entry_price
                print(f"Exit Price: {entry_price}")
                profit = (exit_price - entry_price) * qty
                balance += profit  # Adjust balance
                trade_log.append(f"Stoploss short at {exit_price}, Time: {timestamp}, Loss: {profit}")

            elif timestamp.time() >= pd.to_datetime("15:00:00").time() and position is not None:
                position = None
                exit_price = close_price
                
                profit = (entry_price - close_price) * qty
                profit =  profit if position == "BUY" else -(profit)
                
                win = win+1 if profit>0 else win
                loss = loss+1 if profit<0 else loss

                balance += profit  # Adjust balance
                trade_log.append(f"Squared off at {exit_price}, Time: {timestamp}, Loss/Profit: {profit}")



            # Calculate Win %
            
            total_trades = win + loss
            win_percentage = (win / total_trades * 100) if total_trades > 0 else 0

        

    except Exception as e:
        print(f"Error fetching {stock}: {e}")

    return win, loss, balance



totalLoss = 0
totalWins = 0
totalBalance = 0
capital = 14000
for stock in nifty50_tickers:
        
        # Backtest Variables
        initial_balance = 10000  # Starting capital
        
        trade_log = []
        
        stockWins, stockLoss, balance = check_trades(stock)
        if trade_log:
            i+=1
            print(f"\nSignals for the stock: {stock}")
            print(f"Trade: {i}")
            print("\n".join(trade_log))
            #send_telegram_message(f"\nSignals for the stock: {stock}\n")
            #send_telegram_message("\n".join(trade_log))

        totalLoss += stockLoss
        totalWins += stockWins
        totalBalance += balance
           
         


# Print Results
print("\n📊 Backtest Results:")
        #print(f"Initial Balance: ₹{initial_balance}")
        #print(f"Final Balance: ₹{balance}")
#print(f"Total Trades: {total_trades}")
print(f"Wins: {totalWins}, Losses: {totalLoss}")
print(f"Win %: {(totalWins/(totalWins + totalLoss)) * 100}")
print(f"Profit made: {totalBalance}")
#print(f"Win %: {win_percentage:.2f}%")
        #print("\nTrade Log:")
        #print("\n".join(trade_log))

