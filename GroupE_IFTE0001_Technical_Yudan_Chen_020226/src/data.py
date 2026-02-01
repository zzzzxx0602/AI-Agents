import yfinance as yf
import pandas as pd

def fetch_data(ticker, start_date, end_date=None):
    """
    Fetch data from yfinance and ensure a clean, single-ticker DataFrame.
    """
    print(f"Downloading data for {ticker} from {start_date}...")
    df = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=True)
    
    if df.empty:
        raise ValueError(f"No data found for {ticker}.")

    # Handle yfinance MultiIndex columns 
    if isinstance(df.columns, pd.MultiIndex):
        try:
            df = df.xs(ticker, axis=1, level=1)
        except:
            # Fallback for alternative structures
            df.columns = df.columns.get_level_values(0)

    # Standardize column names
    if 'Close' not in df.columns and 'Adj Close' in df.columns:
        df['Close'] = df['Adj Close']
    
    df = df.reset_index()
    # Calculate daily log returns for quantitative metrics
    df['returns'] = df['Close'].pct_change().fillna(0)
    
    return df