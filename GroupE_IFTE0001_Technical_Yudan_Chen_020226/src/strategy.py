import numpy as np
import pandas as pd
from indicators import calculate_rolling_volatility, calculate_sma

class TurtleAgent:
    """
    Logic:
    1. Regime: Price > SMA 200.
    2. Entry: 20-Day Breakout.
    3. Exit: 10-Day Breakdown.
    """
    def __init__(self, df):
        self.df = df.copy()

    def generate_signals(self, config):
        # 1. Indicators
        self.df['sma_200'] = calculate_sma(self.df['Close'], config.SMA_WINDOW)
        self.df['vol'] = calculate_rolling_volatility(self.df['returns'], window=config.VOL_LOOKBACK)
        
        # Donchian Channels
        self.df['upper_20'] = self.df['Close'].rolling(window=config.ENTRY_WINDOW).max().shift(1)
        self.df['lower_10'] = self.df['Close'].rolling(window=config.EXIT_WINDOW).min().shift(1)
        
        # 2. Signal Logic
        signals = np.zeros(len(self.df))
        state = 0 # 0=Cash, 1=Long
        
        close = self.df['Close'].values
        upper = self.df['upper_20'].values
        lower = self.df['lower_10'].values
        sma = self.df['sma_200'].values
        
        for i in range(1, len(self.df)):
            # Entry: Breakout AND Bull Regime
            if close[i] > upper[i] and close[i] > sma[i]:
                state = 1
            # Exit: Breakdown OR Bear Regime (Hard Stop)
            elif close[i] < lower[i] or close[i] < sma[i]:
                state = 0
            
            signals[i] = state
            
        self.df['signal_state'] = signals

        # 3. Volatility Sizing
        self.df['raw_leverage'] = (config.VOL_TARGET / self.df['vol']).replace([np.inf, -np.inf], 0).fillna(0)
        
        # 4. Apply Leverage
        self.df['leverage'] = self.df['raw_leverage'] * self.df['signal_state']
        self.df['leverage'] = self.df['leverage'].clip(upper=config.MAX_LEVERAGE)
        
        # 5. Lag (Trade T+1)
        self.df['leverage'] = self.df['leverage'].shift(1).fillna(0)
        
        return self.df