import yfinance as yf
import pandas as pd

def get_data(ticker, start, end):
    """
    Fetches OHLCV data from Yahoo Finance.
    Includes robust error handling for MultiIndex columns and Timezone issues.
    """
    print(f"Fetching data for {ticker}...")
    
    try:
        # Download data with auto-adjustment for splits and dividends
        data = yf.download(ticker, start=start, end=end, interval="1d", progress=False, auto_adjust=True)
    except Exception as e:
        raise ValueError(f"yfinance download failed: {e}")
    
    if data is None or data.empty:
        raise ValueError(f"No data fetched for {ticker}. Check internet connection or ticker symbol.")

    # --- Data Cleaning & Formatting ---
    
    # Flatten MultiIndex columns if present (e.g., ('Close', 'AMZN') -> 'Close')
    if isinstance(data.columns, pd.MultiIndex):
        try:
            data.columns = data.columns.get_level_values(0)
        except IndexError:
            pass
    
    # Fallback: Handle tuple columns if not strictly MultiIndex
    if isinstance(data.columns[0], tuple):
        data.columns = [c[0] for c in data.columns]

    # Standardize column names (Capitalize, strip whitespace)
    data.columns = [str(c).strip().capitalize() for c in data.columns]
    
    # Remove Timezone information to ensure compatibility with backtesting logic
    if data.index.tz is not None:
        data.index = data.index.tz_localize(None)

    # Validate required columns
    required_cols = ['Close', 'High', 'Low', 'Open']
    missing_cols = [c for c in required_cols if c not in data.columns]
    if missing_cols:
        raise ValueError(f"Missing columns: {missing_cols}")

    # Drop any initial rows with NaN values (clean start)
    data = data.dropna()

    if data.empty:
        raise ValueError("Data is empty after cleanup.")

    return data