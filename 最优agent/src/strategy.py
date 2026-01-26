import pandas as pd
import numpy as np
from src.indicators import supertrend, chandelier_exit_long

def build_features(
    df: pd.DataFrame, 
    atr_period: int = 10, 
    st_mult: float = 3.0, 
    chandelier_lookback: int = 22, 
    chandelier_k: float = 3.0
) -> pd.DataFrame:
    """
    Computes technical indicators and attaches them to the dataframe.
    """
    df = df.copy()

    # 1. Supertrend
    st_res = supertrend(df, atr_period, st_mult)
    df = df.join(st_res)

    # 2. Chandelier Exit
    df["ChandelierStop"] = chandelier_exit_long(df, df["atr"], chandelier_lookback, chandelier_k)
    
    # Column Renaming for clarity
    df = df.rename(columns={"supertrend": "Supertrend", "st_dir": "ST_Dir", "atr": "ATR"})
    
    return df

def generate_signals(df: pd.DataFrame, enable_reentry: bool = True) -> pd.DataFrame:
    """
    Generates entry and exit signals based on indicators.
    """
    df = df.copy()
    
    # Entry Condition:
    # Supertrend is Bullish (1)
    # Logic: Enter on a flip, OR re-enter if bullish
    
    st_bullish = df["ST_Dir"] == 1
    st_flip = (df["ST_Dir"] == 1) & (df["ST_Dir"].shift(1) == -1)
    
    if enable_reentry:
        entry_signal = st_bullish
    else:
        entry_signal = st_flip
        
    # Exit Condition:
    # 1. Price closes below Chandelier Stop
    # 2. OR Supertrend flips to Bearish
    
    close_below_chandelier = df["Close"] < df["ChandelierStop"]
    st_bearish = df["ST_Dir"] == -1
    
    exit_signal = close_below_chandelier | st_bearish

    df["entry_long"] = entry_signal
    df["exit_long"] = exit_signal
    
    return df