# src/data.py
import pandas as pd
import yfinance as yf

def load_price_data(ticker: str, start="2015-01-01", end=None) -> pd.DataFrame:
    df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]

    if "Close" not in df.columns:
        raise KeyError(f"'Close' not found in yfinance output columns: {list(df.columns)}")

    out = df[["Close"]].copy()
    out.index = pd.to_datetime(out.index)
    return out.sort_index().dropna()
