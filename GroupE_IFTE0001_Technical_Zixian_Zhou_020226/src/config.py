class Config:
    # --- Basic Simulation Settings ---
    TICKER = "AMZN"
    START_DATE = "2015-01-01"
    END_DATE = None
    INITIAL_CAPITAL = 10000

    # --- Technical Indicator Parameters ---
    # EMA 40: Used as the primary trend baseline (Dynamic Support/Resistance)
    EMA_SHORT = 40
    EMA_LONG = 200  # Calculated but currently optional in logic

    # MACD Settings (Standard Momentum)
    MACD_FAST = 12
    MACD_SLOW = 26
    MACD_SIGNAL = 9

    # RSI Settings (Overbought/Oversold levels)
    RSI_PERIOD = 14
    
    # ATR Settings (Used for volatility reference)
    ATR_PERIOD = 14

    # --- Transaction Cost Model ---
    # Commission: 0.1% per trade (buy or sell)
    COMMISSION = 0.001
    # Slippage: 0.1% price impact (simulates execution friction)
    SLIPPAGE = 0.001

    # --- Risk Management ---
    # Volatility Targeting: Adjust position size based on market volatility
    USE_VOL_TARGET = True
    MAX_LEVERAGE = 1.0  # Cap leverage at 1.0x (Cash Only)

    # Stop Loss Settings
    STOP_LOSS_PCT = 0.15      # Hard stop at 15% loss from entry
    TRAILING_STOP_PCT = 0.15  # Trailing stop to lock in profits
    
    # Chandelier Exit (ATR-based stop) - Disabled for this version
    USE_ATR_STOP = False
    ATR_MULTIPLIER = 3.0

    # --- OpenAI API Configuration ---
    OPENAI_API_KEY = "INSERT YOUR API KEY..."