# src/strategy.py
import numpy as np
import pandas as pd
from indicators import calculate_rolling_volatility, calculate_sma, calculate_rsi
from config import VOL_WINDOW, TARGET_VOL, MAX_LEVERAGE, SMA_WINDOW, RSI_WINDOW, RSI_HIGH, REBALANCE_THRESHOLD

# --- Configuration: Exit Buffer Threshold ---
# Loosened to 10% (0.10) to prioritize CAGR.
# We only liquidate to Cash if price drops > 10% below the SMA.
# This tolerates significant corrections (e.g., -15% to -20% from peak)
# and only exits during catastrophic trend collapses (e.g., Dot-com, GFC).
EXIT_BUFFER = 0.10 

class VolatilityStrategy:
    def __init__(self, df):
        """
        Initialize strategy with data.
        """
        self.df = df.copy()

    def calculate_indicators(self):
        """Calculate technical indicators (Vol, SMA, RSI)."""
        self.df['rolling_vol'] = calculate_rolling_volatility(self.df['returns'], window=VOL_WINDOW)
        self.df['sma'] = calculate_sma(self.df['Close'], window=SMA_WINDOW)
        self.df['rsi'] = calculate_rsi(self.df['Close'], window=RSI_WINDOW)
        return self.df

    def generate_signals(self):
        """
        Generate trading signals with Ultra-Loose Risk Control.
        """
        if 'rolling_vol' not in self.df.columns:
            self.calculate_indicators()

        # 1. Base Leverage Calculation (Volatility Targeting)
        # Calculates how much leverage to take based on current market volatility
        safe_vol = self.df['rolling_vol'].replace(0, np.nan)
        self.df['raw_leverage'] = TARGET_VOL / safe_vol
        
        # 2. Dynamic Risk Caps (Stepped Logic)
        self.df['dynamic_cap'] = MAX_LEVERAGE
        
        # --- [Core Logic Update] Extreme Bear Filters ---
        
        # Phase 1: Warning Zone (Price < SMA but within 10% buffer)
        # Action: Reduce leverage to 1.0x (Defensive Mode).
        # Rationale: Do not exit. Ride out the correction to capture the V-shape recovery.
        weak_bear_mask = self.df['Close'] < self.df['sma']
        self.df.loc[weak_bear_mask, 'dynamic_cap'] = 1.0
        
        # Phase 2: Catastrophe Protection (Price < SMA * 0.90)
        # Action: Full Exit to Cash (0.0x).
        # Rationale: Only exit if the trend is completely broken (>10% below SMA).
        # This acts as a "Circuit Breaker" for extreme crashes.
        deep_bear_threshold = self.df['sma'] * (1 - EXIT_BUFFER)
        deep_bear_mask = self.df['Close'] < deep_bear_threshold
        self.df.loc[deep_bear_mask, 'dynamic_cap'] = 0.0
        
        # Phase 3: Momentum Filter (Overbought Protection)
        # Action: Trim exposure if RSI is too high.
        rsi_mask = self.df['rsi'] > RSI_HIGH
        self.df.loc[rsi_mask, 'dynamic_cap'] = 0.8

        # 3. Determine Final Target Leverage
        target_series = self.df[['raw_leverage', 'dynamic_cap']].min(axis=1).clip(lower=0.0)
        
        # 4. Rebalance Buffer (Reduce Transaction Costs)
        executed_leverage = []
        current_lev = 0.0
        
        for target in target_series.values:
            if np.isnan(target):
                executed_leverage.append(0.0)
                continue
            
            # Case A: Hard Exit (0.0) -> Execute immediately
            if target == 0.0:
                current_lev = 0.0
            # Case B: New Entry (0.0 to >0.0) -> Execute immediately
            elif current_lev == 0.0 and target > 0.0:
                current_lev = target
            # Case C: Standard Rebalancing -> Only trade if change > threshold
            elif abs(target - current_lev) > REBALANCE_THRESHOLD:
                current_lev = target
            
            executed_leverage.append(current_lev)

        self.df['leverage'] = executed_leverage
        
        # 5. Signal Lag (Execute on T+1 open/close)
        self.df['leverage'] = self.df['leverage'].shift(1).fillna(0)

        return self.df

    def calculate_returns(self, cost_bps=10, risk_free_rate=0.04):
        """Calculate Net Strategy Returns (Net of costs & financing)."""
        # 1. Equity Component
        stock_component = self.df['leverage'] * self.df['returns']
        
        # 2. Cash/Financing Component
        rf_daily = risk_free_rate / 252
        cash_weight = 1.0 - self.df['leverage']
        cash_component = cash_weight * rf_daily
        
        # 3. Transaction Costs
        pos_change = self.df['leverage'].diff().abs().fillna(0)
        cost_rate = cost_bps / 10000
        txn_costs = pos_change * cost_rate
        
        # Total Net Return
        self.df['strategy_returns'] = stock_component + cash_component - txn_costs
        
        return self.df