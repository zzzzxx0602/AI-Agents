import pandas as pd

def generate_signals(df):
    """
    Strategy Logic: Dynamic Trend Following (EMA 40).
    
    Entry Conditions:
    1. Price is above EMA 40 by 1% (Trend Confirmation).
    2. MACD is Bullish (Momentum Confirmation).
    3. RSI is below 85 (Not Overbought).
    
    Exit Conditions:
    1. Price drops below EMA 40 (Trend Reversal).
    """
    df = df.copy()

    # --- 1. Core Trend Logic ---
    # Filter: Price must be > EMA 40 with a 1% buffer to avoid noise
    valid_breakout = df['Close'] > (df['EMA_Short'] * 1.01)

    # --- 2. Momentum & Oscillation Filters ---
    # Filter: MACD Line > Signal Line indicates positive momentum
    macd_bullish = df['MACD_Line'] > df['Signal_Line']
    
    # Filter: RSI < 85 indicates there is still room for upside
    rsi_safe = df['RSI'] < 85

    # --- 3. Signal Generation ---
    # Buy Signal: All conditions must be met
    buy_signal = valid_breakout & macd_bullish & rsi_safe

    # Sell Signal: Trend is broken (Price crosses below EMA)
    sell_signal = (df['Close'] < df['EMA_Short'])

    df['Bullish_Condition'] = buy_signal
    df['Bearish_Condition'] = sell_signal

    return df