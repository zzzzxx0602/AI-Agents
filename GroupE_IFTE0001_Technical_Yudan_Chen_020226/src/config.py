import os

# --- Identity ---
STRATEGY_NAME = "Enhanced Turtle (Trend + Volatility)"
TICKER = "AMZN"
START_DATE = "2015-01-01"

# --- Strategy Logic ---
# 1. Regime: Price > SMA 200 (Bull Market Filter)
# 2. Entry: Breakout 20-Day High (Fast Momentum)
# 3. Exit: Breakdown 10-Day Low (Trailing Stop)
ENTRY_WINDOW = 20      
EXIT_WINDOW = 10       
SMA_WINDOW = 200       

# --- Risk Management ---
VOL_TARGET = 0.30      # Target 30% Volatility
MAX_LEVERAGE = 1.5     
VOL_LOOKBACK = 20

# --- Costs ---
COST_BPS = 10 
RISK_FREE_RATE = 0.04