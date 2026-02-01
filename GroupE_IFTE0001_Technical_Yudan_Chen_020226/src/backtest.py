import numpy as np
import pandas as pd

def run_backtest(df, config):
    """
    Executes backtest with Financing Costs, Interest Income, and Trade Stats.
    """
    df = df.copy()
    daily_rf = config.RISK_FREE_RATE / 252
    
    # 1. Component Returns
    # stock_component: Return from the leveraged equity portion
    df['stock_component'] = df['leverage'] * df['returns']
    
    # Financing / Cash Logic
    # Lev > 1.0 (Borrowing) -> Cash weight negative -> Pay Interest
    # Lev < 1.0 (Idle Cash) -> Cash weight positive -> Earn Interest
    df['cash_weight'] = 1.0 - df['leverage']
    df['cash_component'] = df['cash_weight'] * daily_rf
    
    # Transaction Costs 
    df['pos_change'] = df['leverage'].diff().abs().fillna(0)
    df['cost_drag'] = df['pos_change'] * (config.COST_BPS / 10000)
    
    # 2. Total Net Strategy Return 
    df['strategy_returns'] = df['stock_component'] + df['cash_component'] - df['cost_drag']
    
    # 3. Equity Curves
    df['strategy_equity'] = (1 + df['strategy_returns']).cumprod()
    df['benchmark_equity'] = (1 + df['returns']).cumprod()
    
    # 4. Metrics Calculation
    def get_metrics(returns, equity):
        days = len(returns)
        if days < 252: return 0.0, 0.0, 0.0, 0.0
        
        cagr = (equity.iloc[-1])**(252/days) - 1
        vol = returns.std() * np.sqrt(252)
        
        peak = equity.cummax()
        dd = (equity - peak) / peak
        mdd = dd.min()
        
        sharpe = (cagr - config.RISK_FREE_RATE) / vol if vol > 0 else 0
        calmar = abs(cagr / mdd) if mdd != 0 else 0
        
        return cagr, mdd, sharpe, calmar

    # Calculate Trade Statistics 
    trades = []
    in_trade = False
    entry_idx = 0
    equity_vals = df['strategy_equity'].values
    lev_vals = df['leverage'].values
    
    for i in range(1, len(df)):
        # Entry: Yesterday 0, Today > 0
        if lev_vals[i-1] == 0 and lev_vals[i] > 0:
            in_trade = True
            entry_idx = i
        # Exit: Yesterday > 0, Today 0 (or End of Data)
        elif (lev_vals[i-1] > 0 and lev_vals[i] == 0) or (in_trade and i == len(df)-1):
            in_trade = False
            pnl = (equity_vals[i] / equity_vals[entry_idx]) - 1
            trades.append(pnl)
            
    trades = np.array(trades)
    win_rate = np.sum(trades > 0) / len(trades) if len(trades) > 0 else 0.0
    
    # Compute Final Metrics
    s_cagr, s_mdd, s_sharpe, s_calmar = get_metrics(df['strategy_returns'], df['strategy_equity'])
    b_cagr, b_mdd, b_sharpe, b_calmar = get_metrics(df['returns'], df['benchmark_equity'])
    
    metrics = {
        'strat_cagr': s_cagr, 'strat_max_dd': s_mdd, 'strat_sharpe': s_sharpe, 'strat_calmar': s_calmar,
        'bh_cagr': b_cagr, 'bh_max_dd': b_mdd, 'bh_sharpe': b_sharpe, 'bh_calmar': b_calmar,
        'hit_rate': win_rate, 'total_trades': len(trades)
    }
    
    return df, metrics