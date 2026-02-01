import numpy as np
import pandas as pd

def calculate_rolling_volatility(returns_series, window=20, ann_factor=252):
    """
    Calculate annualized rolling volatility.
    Used for: Position Sizing (Volatility Targeting).
    """
    return returns_series.rolling(window=window).std() * np.sqrt(ann_factor)

def calculate_sma(series, window=200):
    """
    Calculate Simple Moving Average.
    Used for: Regime Filter (Bull/Bear Market detection).
    """
    return series.rolling(window=window).mean()

