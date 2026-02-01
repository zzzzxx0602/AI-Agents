# src/backtest.py
import numpy as np
import pandas as pd
from strategy import VolatilityStrategy
from config import COST_BPS, RISK_FREE_RATE

def calculate_max_drawdown(equity_curve):
    """Calculate Max Drawdown (Maximum percentage drop from peak)."""
    peak = equity_curve.cummax()
    drawdown = (equity_curve - peak) / peak
    return drawdown.min()

def calculate_sharpe_ratio(returns, risk_free_rate=0.0):
    """
    Calculate Sharpe Ratio (Risk-adjusted return).
    Formula: (Mean Excess Return / Std Dev) * sqrt(252)
    """
    rf_daily = risk_free_rate / 252.0
    excess_returns = returns - rf_daily
    if excess_returns.std() == 0: return 0.0
    return (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)

def calculate_sortino_ratio(returns, risk_free_rate=0.0):
    """
    Calculate Sortino Ratio.
    (Similar to Sharpe, but penalizes only downside volatility)
    """
    rf_daily = risk_free_rate / 252.0
    excess_returns = returns - rf_daily
    # Use only negative returns for standard deviation
    downside_returns = excess_returns[excess_returns < 0]
    downside_std = downside_returns.std()
    if downside_std == 0: return 0.0
    return (excess_returns.mean() * 252) / (downside_std * np.sqrt(252))

def calculate_calmar_ratio(cagr, max_dd):
    """
    Calculate Calmar Ratio.
    Formula: Annualized Return / |Max Drawdown|
    """
    if max_dd == 0: return 0.0
    return cagr / abs(max_dd)

def calculate_cagr(equity_curve):
    """Calculate Compound Annual Growth Rate (CAGR)."""
    if len(equity_curve) < 2: return 0.0
    start_date = pd.to_datetime(equity_curve.index[0])
    end_date = pd.to_datetime(equity_curve.index[-1])
    days = (end_date - start_date).days
    if days <= 0: return 0.0
    years = days / 365.25
    total_return = equity_curve.iloc[-1] / equity_curve.iloc[0]
    if total_return <= 0: return -1.0
    return float(total_return ** (1 / years) - 1)

def _generate_trade_log(df):
    """
    Helper: Generate discrete Trade Log from continuous leverage series.
    Rule: Open Trade when Leverage > 0, Close Trade when Leverage == 0.
    """
    trades = []
    in_trade = False
    entry_date = None
    entry_price = 0.0
    entry_equity = 0.0
    max_lev = 0.0
    
    # Ensure index is datetime
    df.index = pd.to_datetime(df.index)
    
    for date, row in df.iterrows():
        lev = row['leverage']
        price = row['Close']
        equity = row['strategy_equity']
        
        # Signal: Open Trade (Leverage goes from 0 to positive)
        if lev > 0 and not in_trade:
            in_trade = True
            entry_date = date
            entry_price = price
            entry_equity = equity
            max_lev = lev
            
        # Signal: Update Status (Track max leverage during holding)
        elif lev > 0 and in_trade:
            max_lev = max(max_lev, lev)
            
        # Signal: Close Trade (Leverage drops to 0)
        elif lev == 0 and in_trade:
            in_trade = False
            # Calculate PnL for this specific trade period (Assume 100k capital for display)
            pnl_abs = (equity - entry_equity) * 100000 
            
            trades.append({
                'entry_date': entry_date,
                'exit_date': date,
                'entry_price': entry_price,
                'exit_price': price,
                'shares': 1000, # Simulated shares
                'leverage_mult_at_entry': max_lev, # Record max leverage used
                'pnl': pnl_abs,
                'exit_reason': 'Risk Off (Vol/SMA Filter)'
            })
            
    # Handle open position at the end of backtest
    if in_trade:
        last_row = df.iloc[-1]
        pnl_abs = (last_row['strategy_equity'] - entry_equity) * 100000
        trades.append({
            'entry_date': entry_date,
            'exit_date': df.index[-1], # Till date
            'entry_price': entry_price,
            'exit_price': last_row['Close'],
            'shares': 1000,
            'leverage_mult_at_entry': max_lev,
            'pnl': pnl_abs,
            'exit_reason': 'Position Open'
        })
        
    return pd.DataFrame(trades)

def run_backtest(df):
    """
    Execute Main Backtest Process.
    Returns: Result DataFrame, Metrics Dictionary, Trades DataFrame.
    """
    # 1. Initialize and Run Strategy
    strategy = VolatilityStrategy(df)
    df = strategy.generate_signals()
    df = strategy.calculate_returns(cost_bps=COST_BPS, risk_free_rate=RISK_FREE_RATE)
    
    # 2. Calculate Equity Curves
    df['strategy_equity'] = (1 + df['strategy_returns']).cumprod()
    df['benchmark_equity'] = (1 + df['returns']).cumprod()
    
    metrics = {}
    
    # --- Benchmark Metrics (Buy & Hold) ---
    metrics['bh_total_return'] = df['benchmark_equity'].iloc[-1] - 1
    metrics['bh_cagr'] = calculate_cagr(df['benchmark_equity'])
    metrics['bh_max_dd'] = calculate_max_drawdown(df['benchmark_equity'])
    metrics['bh_sharpe'] = calculate_sharpe_ratio(df['returns'], RISK_FREE_RATE)
    metrics['bh_sortino'] = calculate_sortino_ratio(df['returns'], RISK_FREE_RATE)
    metrics['bh_calmar'] = calculate_calmar_ratio(metrics['bh_cagr'], metrics['bh_max_dd'])
    
    # --- Strategy Metrics ---
    metrics['strat_total_return'] = df['strategy_equity'].iloc[-1] - 1
    metrics['strat_cagr'] = calculate_cagr(df['strategy_equity'])
    metrics['strat_max_dd'] = calculate_max_drawdown(df['strategy_equity'])
    metrics['strat_sharpe'] = calculate_sharpe_ratio(df['strategy_returns'], RISK_FREE_RATE)
    metrics['strat_sortino'] = calculate_sortino_ratio(df['strategy_returns'], RISK_FREE_RATE)
    metrics['strat_calmar'] = calculate_calmar_ratio(metrics['strat_cagr'], metrics['strat_max_dd'])
    
    # --- Other Statistics ---
    metrics['final_leverage'] = df['leverage'].iloc[-1]
    daily_wins = (df['strategy_returns'] > 0).sum()
    metrics['win_rate'] = daily_wins / len(df) if len(df) > 0 else 0.0
    
    # --- Generate Trade Log ---
    trades_df = _generate_trade_log(df)

    return df, metrics, trades_df