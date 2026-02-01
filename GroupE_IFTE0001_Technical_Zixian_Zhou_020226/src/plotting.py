import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
import os

def plot_performance(df, ticker, initial_capital):
    """
    Generates a comprehensive 4-panel chart:
    1. Equity Curve (Strategy vs Benchmark)
    2. Rolling Volatility (Risk comparison)
    3. Drawdown (Downside comparison)
    4. Position Size (Market Exposure)
    """
    if not os.path.exists("reports"):
        os.makedirs("reports")
        
    # --- Data Preparation ---
    # Benchmark Equity (Buy & Hold)
    benchmark_equity = (df['Close'] / df['Close'].iloc[0]) * initial_capital
    
    # Rolling Volatility (21-day annualized)
    strat_ret = df['Portfolio_Value'].pct_change().fillna(0)
    strat_vol = strat_ret.rolling(window=21).std() * np.sqrt(252)
    
    bench_ret = df['Close'].pct_change().fillna(0)
    bench_vol = bench_ret.rolling(window=21).std() * np.sqrt(252)
    
    # Drawdown Calculation
    strat_max = df['Portfolio_Value'].cummax()
    strat_dd = (df['Portfolio_Value'] - strat_max) / strat_max
    
    bench_max = benchmark_equity.cummax()
    bench_dd = (benchmark_equity - bench_max) / bench_max

    # --- Plotting ---
    # Create 4 vertically stacked subplots
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(12, 18), sharex=True, 
                                             gridspec_kw={'height_ratios': [2, 1, 1, 1]})
    
    # Panel 1: Equity Curve
    ax1.plot(df.index, df['Portfolio_Value'], label='Strategy Equity', color='#2980b9', linewidth=2)
    ax1.plot(df.index, benchmark_equity, label=f'{ticker} Buy & Hold', color='#95a5a6', linestyle='--', linewidth=1.5)
    ax1.set_title(f"{ticker} Strategy Performance Overview", fontsize=14, fontweight='bold')
    ax1.set_ylabel("Account Value ($)")
    ax1.legend(loc="upper left")
    ax1.grid(True, linestyle=':', alpha=0.6)
    
    # Panel 2: Rolling Volatility
    ax2.plot(df.index, strat_vol, label='Strategy Volatility (21d)', color='#e67e22', linewidth=1.5)
    ax2.plot(df.index, bench_vol, label='Benchmark Volatility', color='#bdc3c7', linewidth=1, linestyle=':')
    ax2.set_title("Rolling Volatility (Risk)", fontsize=12)
    ax2.set_ylabel("Annualized Std Dev")
    ax2.legend(loc="upper left")
    ax2.grid(True, linestyle=':', alpha=0.6)
    
    # Panel 3: Drawdown
    ax3.fill_between(df.index, strat_dd, 0, color='#e74c3c', alpha=0.3, label='Strategy Drawdown')
    ax3.plot(df.index, strat_dd, color='#c0392b', linewidth=1)
    ax3.plot(df.index, bench_dd, color='#7f8c8d', linewidth=1, linestyle=':', label='Benchmark Drawdown')
    ax3.set_title("Drawdown Profile", fontsize=12)
    ax3.set_ylabel("Drawdown %")
    ax3.legend(loc="lower left")
    ax3.grid(True, linestyle=':', alpha=0.6)
    
    # Panel 4: Position Size
    if 'Position' in df.columns:
        ax4.plot(df.index, df['Position'], label='Position (Shares)', color='#8e44ad', linewidth=1.5, drawstyle='steps-post')
        ax4.fill_between(df.index, df['Position'], 0, step='post', color='#8e44ad', alpha=0.1)
    else:
        ax4.text(0.5, 0.5, "Position Data Not Available", ha='center', va='center')
        
    ax4.set_title("Position Size (Market Exposure)", fontsize=12)
    ax4.set_ylabel("Shares")
    ax4.grid(True, linestyle=':', alpha=0.6)
    
    # X-axis formatting
    plt.xlabel("Date")
    ax4.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax4.xaxis.set_major_locator(mdates.YearLocator())
    
    plt.tight_layout()
    plt.savefig("reports/performance_summary.png", dpi=100)
    plt.close()