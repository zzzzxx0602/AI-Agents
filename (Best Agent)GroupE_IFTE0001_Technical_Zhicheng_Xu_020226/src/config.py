# src/config.py

# --- Ticker and Date ---
TICKER = "AMZN"
START_DATE = "2015-01-01"
END_DATE = None  # None means up to today

# --- Core Strategy Parameters (Volatility Targeting) ---
VOL_WINDOW = 20    # Lookback window for realized volatility
TARGET_VOL = 0.25  # Target annualized volatility (25% for tech stocks)
MAX_LEVERAGE = 1.5 # Maximum allowed leverage ratio

# --- Risk Filters (Trend & Momentum) ---
SMA_WINDOW = 200   # Trend Filter: Price < SMA200 -> Bearish -> Cap Leverage at 1.0x
RSI_WINDOW = 14    # Momentum Indicator
RSI_HIGH = 80      # Overbought Threshold: RSI > 80 -> Trim Exposure

# --- Real World Parameters (Costs & Cash) ---
COST_BPS = 10          # Transaction Cost: 10bps (0.1%)
RISK_FREE_RATE = 0.04  # Risk-Free Rate: 4% (Yield on idle cash / Cost of borrowing)
REBALANCE_THRESHOLD = 0.10 # Rebalance Buffer: Only trade if target differs by >10%