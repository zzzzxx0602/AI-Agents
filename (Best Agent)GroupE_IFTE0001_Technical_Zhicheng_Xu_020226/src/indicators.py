# src/indicators.py
import numpy as np
import pandas as pd

def calculate_rolling_volatility(returns_series, window=20, ann_factor=252):
    """
    Calculate annualized rolling volatility.
    (Core metric for Volatility Targeting Strategy)
    """
    return returns_series.rolling(window=window).std() * np.sqrt(ann_factor)

def calculate_sma(series, window=200):
    """
    Calculate Simple Moving Average (SMA).
    (Used for long-term trend filtering, e.g., 200-day SMA for Bull/Bear regime)
    """
    return series.rolling(window=window).mean()

def calculate_rsi(series, window=14):
    """
    Calculate Relative Strength Index (RSI).
    (Used for momentum and overbought/oversold detection)
    """
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    
    # Calculate average gain/loss using rolling mean
    avg_gain = gain.rolling(window=window, min_periods=window).mean()
    avg_loss = loss.rolling(window=window, min_periods=window).mean()
    
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    
    # Fill NaN values with 50 (Neutral)
    return rsi.fillna(50)