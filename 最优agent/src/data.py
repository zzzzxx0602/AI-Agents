import pandas as pd
import yfinance as yf

REQUIRED_COLS = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]

def download_ohlcv(ticker: str, start: str, end: str | None = None) -> pd.DataFrame:
    df = yf.download(
        tickers=ticker,
        start=start,
        end=end,
        auto_adjust=False,
        progress=False,
        actions=False,
        threads=True,
    )
    if df is None or df.empty:
        raise ValueError(f"No data returned for ticker={ticker}.")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.copy()

def load_ohlcv_from_csv(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date")
    else:
        df.index = pd.to_datetime(df.index)

    rename_map = {
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "adj_close": "Adj Close",
        "adj close": "Adj Close",
        "volume": "Volume",
    }
    df = df.rename(columns={c: rename_map.get(c.lower(), c) for c in df.columns})

    if "Adj Close" not in df.columns and "Close" in df.columns:
        df["Adj Close"] = df["Close"]

    df = df.sort_index()
    return df

def validate_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}. Got columns: {list(df.columns)}")
    df = df.dropna(subset=["Open", "High", "Low", "Close"]).copy()
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    if (df["High"] < df["Low"]).any():
        raise ValueError("Found rows where High < Low (invalid OHLC data).")
    return df
