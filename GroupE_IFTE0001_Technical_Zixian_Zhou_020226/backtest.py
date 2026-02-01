import pandas as pd
import numpy as np

def calculate_position_size_simple(cash, method="all_in"):
    """
    Simple fallback for position sizing.
    """
    if method == "all_in":
        return cash * 0.99 
    return cash * 0.5

def run_backtest(df, initial_capital=10000, commission=0.001, slippage=0.001, 
                 trailing_stop_pct=0.15, stop_loss_pct=0.15,
                 use_atr=False, atr_multiplier=3.0,
                 use_vol_target=False, max_leverage=1.0): 
    """
    Executes the backtest simulation over the provided DataFrame.
    Returns the equity curve, trade log, and performance metrics.
    """
    cash = initial_capital
    position = 0
    entry_price = 0
    highest_price_since_entry = 0 
    
    # Variables to track trade state for logging
    current_entry_date = None
    current_entry_leverage = 0.0
    
    portfolio_values = []
    position_history = []  # Tracks daily shares held
    closed_trades = []     # Stores completed round-trip trades
    
    # --- 1. Pre-calculate Volatility for Position Sizing ---
    df = df.copy()
    df['Returns'] = df['Close'].pct_change()
    
    # Calculate annualized volatility windows
    df['Vol_Short'] = df['Returns'].rolling(window=21).std() * np.sqrt(252)
    df['Vol_Long'] = df['Returns'].rolling(window=252).std() * np.sqrt(252)
    
    # Fill NaN volatility values to avoid calculation errors
    df['Vol_Long'] = df['Vol_Long'].fillna(df['Vol_Short']).fillna(0.20)
    df['Vol_Short'] = df['Vol_Short'].fillna(0.20)
    
    vol_short_arr = df['Vol_Short'].values
    vol_long_arr = df['Vol_Long'].values
    
    # Extract data to numpy arrays for performance iteration
    dates = df.index
    opens = df['Open'].values
    closes = df['Close'].values
    highs = df['High'].values
    lows = df['Low'].values
    atrs = df['ATR'].values if 'ATR' in df.columns else np.zeros(len(df))
    
    bullish = df['Bullish_Condition'].values
    bearish = df['Bearish_Condition'].values
    
    risk_free_daily = 0.03 / 365
    
    # --- 2. Main Simulation Loop ---
    for i in range(len(df) - 1):
        # A. Accrue Interest on idle cash
        if cash > 0:
            cash += cash * risk_free_daily
        
        # Mark-to-Market Valuation
        current_val = cash + (position * closes[i])
        portfolio_values.append(current_val)
        position_history.append(position)
        
        # B. Risk Management Checks (Stops)
        force_sell = False
        exit_reason = ""
        
        if position > 0:
            # Update high-water mark for trailing stop
            if highs[i] > highest_price_since_entry:
                highest_price_since_entry = highs[i]
            
            # Check Trailing Stop (Dynamic ATR or Fixed %)
            if use_atr:
                stop_price = highest_price_since_entry - (atrs[i] * atr_multiplier)
                if closes[i] < stop_price:
                    force_sell = True
                    exit_reason = f"CHAND_STOP"
            else:
                drawdown = (highest_price_since_entry - closes[i]) / highest_price_since_entry
                if drawdown > trailing_stop_pct:
                    force_sell = True
                    exit_reason = f"TRAIL_STOP"
                
            # Check Hard Stop Loss (Fixed % from entry)
            if not force_sell:
                hit_low_pct = (entry_price - lows[i]) / entry_price
                if hit_low_pct > stop_loss_pct:
                    force_sell = True
                    exit_reason = f"HARD_STOP"

        # C. Trade Execution (Logic applies to Next Day Open)
        next_open = opens[i+1]
        next_date = dates[i+1]
        
        # --- SELL Logic ---
        if position > 0 and (bearish[i] or force_sell):
            raw_price = next_open
            # Apply Slippage (Sell lower)
            sell_price = raw_price * (1 - slippage)
            
            revenue = position * sell_price
            cost = revenue * commission
            cash += (revenue - cost)
            
            pnl = (sell_price - entry_price) * position - cost
            
            # Record Closed Trade
            reason_str = exit_reason if force_sell else "SIGNAL_EXIT"
            closed_trades.append({
                "entry_date": current_entry_date,
                "exit_date": next_date,
                "entry_price": entry_price,
                "exit_price": sell_price,
                "shares": position,
                "leverage_mult_at_entry": current_entry_leverage,
                "pnl": pnl,
                "exit_reason": reason_str
            })
            
            # Reset Position State
            position = 0
            entry_price = 0
            highest_price_since_entry = 0
            
        # --- BUY Logic ---
        elif position == 0 and bullish[i]:
            raw_price = next_open
            # Apply Slippage (Buy higher)
            buy_price = raw_price * (1 + slippage)
            
            # Determine Position Size (Volatility Targeting)
            leverage = 1.0
            if use_vol_target:
                curr_vol = vol_short_arr[i]
                avg_vol = vol_long_arr[i]
                # Safety checks
                if curr_vol < 0.05: curr_vol = 0.05
                if avg_vol < 0.05: avg_vol = 0.05
                
                # Scale inverse to volatility
                leverage = avg_vol / curr_vol
                leverage = min(leverage, max_leverage) 
                leverage = max(leverage, 0.5) 
                invest_amt = cash * leverage
            else:
                invest_amt = calculate_position_size_simple(cash)
            
            # Calculate shares
            shares = invest_amt / (buy_price * (1 + commission))
            cost = shares * buy_price * (1 + commission)
            
            cash -= cost
            position = shares
            entry_price = buy_price
            highest_price_since_entry = buy_price
            
            # Record Entry State
            current_entry_date = next_date
            current_entry_leverage = leverage

    # --- Finalize Data ---
    # Append last day state
    portfolio_values.append(cash + (position * closes[-1]))
    position_history.append(position)
    
    # Sync lengths with DataFrame
    if len(portfolio_values) == len(df):
        df['Portfolio_Value'] = portfolio_values
        df['Position'] = position_history
    else:
        df['Portfolio_Value'] = pd.Series(portfolio_values, index=df.index[:len(portfolio_values)])
        df['Position'] = pd.Series(position_history, index=df.index[:len(position_history)])
        
    trades_df = pd.DataFrame(closed_trades)
    metrics = calculate_metrics(df, trades_df, initial_capital)
    
    return df, trades_df, metrics

def _compute_series_metrics(equity_series, initial_capital):
    """Helper to compute standard financial metrics."""
    final_value = equity_series.iloc[-1]
    total_return = (final_value - initial_capital) / initial_capital
    days = (equity_series.index[-1] - equity_series.index[0]).days
    cagr = (final_value / initial_capital) ** (365.25 / days) - 1 if days > 0 else 0
    running_max = equity_series.cummax()
    drawdown = (equity_series - running_max) / running_max
    max_drawdown = drawdown.min()
    daily_returns = equity_series.pct_change().dropna()
    if daily_returns.std() > 0:
        excess_returns = daily_returns - (0.03 / 252) 
        sharpe = (excess_returns.mean() / daily_returns.std()) * np.sqrt(252)
    else:
        sharpe = 0
    return {"Total Return": total_return, "CAGR": cagr, "Max Drawdown": max_drawdown, "Sharpe Ratio": sharpe}

def calculate_metrics(df, trades_df, initial_capital):
    """Calculates metrics for the active strategy."""
    metrics = _compute_series_metrics(df['Portfolio_Value'], initial_capital)
    
    hit_rate = 0
    if not trades_df.empty:
        profitable_trades = trades_df[trades_df['pnl'] > 0]
        hit_rate = len(profitable_trades) / len(trades_df)
            
    metrics["Hit Rate"] = hit_rate
    metrics["Total Trades"] = len(trades_df)
    return metrics

def calculate_benchmark_metrics(df, initial_capital):
    """Calculates metrics for the Buy & Hold benchmark."""
    benchmark_equity = (df['Close'] / df['Close'].iloc[0]) * initial_capital
    b_metrics = _compute_series_metrics(benchmark_equity, initial_capital)
    b_metrics["Hit Rate"] = None 
    b_metrics["Total Trades"] = 0
    return b_metrics