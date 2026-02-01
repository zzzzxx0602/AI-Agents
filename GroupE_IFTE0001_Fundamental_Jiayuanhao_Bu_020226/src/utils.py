import pandas as pd

def safe_loc(df: pd.DataFrame, row_name: str) -> pd.Series:
    """Safely retrieve a row from a Yahoo Finance statement table."""
    if df is None or getattr(df, "empty", True):
        return pd.Series(dtype="float64")
    if row_name in df.index:
        return df.loc[row_name]
    return pd.Series([pd.NA] * df.shape[1], index=df.columns)

def normalize_year_index(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.index, pd.DatetimeIndex):
        df = df.copy()
        df.index = df.index.year.astype(str)
    return df
