# src/data.py
import yfinance as yf
import pandas as pd

def fetch_data(ticker, start_date, end_date=None):
    """
    Fetch data from Yahoo Finance and calculate basic daily returns.
    """
    print(f"Downloading data for {ticker} from {start_date}...")
    
    # auto_adjust=True handles stock splits and dividends automatically
    df = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=True)
    
    if df.empty:
        raise ValueError(f"No data found for {ticker}. Please check the ticker symbol or date range.")

    # --- Data Cleaning (Compatible with different yfinance versions) ---
    # If MultiIndex (new yfinance structure), try to extract the specific ticker level
    if isinstance(df.columns, pd.MultiIndex):
        try:
            # Try to get data under 'Close' level
            df = df.xs(ticker, axis=1, level=1)
        except:
            # If fails, structure might already be flat
            pass

    # Ensure 'Close' column exists
    if 'Close' not in df.columns:
        if 'Adj Close' in df.columns:
            df['Close'] = df['Adj Close']
        else:
            # Last resort: take the first column
            df['Close'] = df.iloc[:, 0]
            
    # --- Calculate Daily Returns ---
    # Required for strategy backtesting
    df['returns'] = df['Close'].pct_change().fillna(0)
    
    return df
