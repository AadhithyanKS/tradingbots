import pandas as pd
import yfinance as yf
from tqdm import tqdm  # Import tqdm for progress bar
import pytz 
import pandas_ta as ta
from ta.momentum import RSIIndicator


ist = pytz.timezone("Asia/Kolkata")
# Fetch NIFTY 50 stock list
url = "https://archives.nseindia.com/content/indices/ind_nifty50list.csv"
df = pd.read_csv(url)
nifty50_tickers = [symbol + ".NS" for symbol in df["Symbol"]]
print(f"Tracking {len(nifty50_tickers)} stocks...\n")



# Store historical buy/sell signals
signals_list = []



# Function to Fetch Historical Data & Generate Signals
def analyze_historical_signals(stock):
    try:
        df = yf.download(stock, interval="5m", period="5d", progress=False)
        df.dropna(inplace=True)

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)

        df.index = df.index.tz_convert(ist)

        df["RSI"] = ta.rsi(df["Close"],length = 14)
        
        # Calculate EMAs
        df["EMA_5"] = df["Close"].ewm(span=5, adjust=False).mean()
        df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()
        df["EMA_21"] = df["Close"].ewm(span=21, adjust=False).mean()

        #MACD
        macd_df = ta.macd(df["Close"], fast=12, slow=26, signal=9)
    
        # Assign correct column names
        df["MACD"] = macd_df["MACD_12_26_9"]
        df["MACD_Signal"] = macd_df["MACDs_12_26_9"]        

        # Iterate over historical data (starting from index 1)
        for i in range(1, len(df)):
            timestamp = df.index[i]  # Get the timestamp

            # Extract scalar values using `.item()` (fixing Series ambiguity issue)
            EMA_5_latest = df["EMA_5"].iloc[i].item()
            EMA_20_latest = df["EMA_20"].iloc[i].item()
            ema_21_latest = df["EMA_21"].iloc[i].item()
            EMA_5_previous = df["EMA_5"].iloc[i - 1].item()
            EMA_20_previous = df["EMA_20"].iloc[i - 1].item()
            EMA_5_previous2 = df["EMA_5"].iloc[i - 2].item()
            EMA_20_previous2 = df["EMA_20"].iloc[i - 2].item()
            macdlatest = df["MACD"].iloc[i].item()
            macdSignallatest = df["MACD_Signal"].iloc[i].item()
            RSI_latest = df["RSI"].iloc[i].item()
            #print(RSI_latest)

            # Buy/Sell Conditions
            buy_signal = (EMA_5_latest > EMA_20_latest) and (EMA_5_previous <= EMA_20_previous) and (RSI_latest>50) and (macdlatest>macdSignallatest)
            sell_signal = (EMA_5_latest < EMA_20_latest) and (EMA_5_previous >= EMA_20_previous) and (RSI_latest<50) and (macdlatest<macdSignallatest)

            if buy_signal or sell_signal:
                signal_type = "BUY" if buy_signal else "SELL"
                close_price = df["Close"].iloc[i].item()
                signals_list.append([stock, signal_type, timestamp, close_price,EMA_5_latest,EMA_20_latest,RSI_latest,macdlatest,macdSignallatest])

    except Exception as e:
        print(f"Error fetching {stock}: {e}")

# Run Analysis with Progress Bar
print("🔄 Processing historical data...\n")
for stock in tqdm(nifty50_tickers, desc="Analyzing Stocks", unit="stock"):
    analyze_historical_signals(stock)

# Convert to DataFrame & Save to CSV
signals_df = pd.DataFrame(signals_list, columns=["Stock", "Signal", "Timestamp", "Price","EMA5","EMA20","RSI","MACD","MACD Signal"])
signals_df.to_csv("historical_signals.csv", index=False)

print("\n✅ Historical analysis completed! Check 'historical_signals.csv' for results.")
