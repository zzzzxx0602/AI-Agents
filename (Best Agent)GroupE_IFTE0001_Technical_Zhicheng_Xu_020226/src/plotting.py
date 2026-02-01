# src/plotting.py
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
from config import VOL_WINDOW, TARGET_VOL

def plot_results(df, output_dir="reports", filename="backtest_chart.png"):
    """
    Plot Professional 4-Panel Backtest Charts:
    1. Net Equity Curve
    2. Drawdown Profile
    3. Volatility Regime
    4. Leverage & Risk Controls
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Set transparent background style (optimized for HTML embedding)
    plt.rcParams.update({
        "figure.facecolor":  (0.0, 0.0, 0.0, 0.0),  # Transparent
        "axes.facecolor":    (0.0, 0.0, 0.0, 0.0),  # Transparent
        "savefig.facecolor": (0.0, 0.0, 0.0, 0.0),  # Transparent
    })
    
    # Define Colors
    STRAT_COLOR = "#0044cc"  # Tech Blue (Strategy)
    BENCH_COLOR = "#ff8c00"  # Vibrant Orange (Benchmark)
    VOL_COLOR   = "#d62728"  # Alert Red (Volatility)

    # Calculate Rolling Volatility (For visualization)
    rolling_strat_vol = df['strategy_returns'].rolling(window=VOL_WINDOW).std() * np.sqrt(252)
    rolling_bench_vol = df['returns'].rolling(window=VOL_WINDOW).std() * np.sqrt(252)

    # Create 4x1 Subplots
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(10, 14), sharex=True)
    
    # --- Panel 1: Cumulative Returns (Log Scale) ---
    ax1.plot(df.index, df['strategy_equity'], label='Strategy (Net)', color=STRAT_COLOR, lw=2)
    ax1.plot(df.index, df['benchmark_equity'], label='Benchmark (Buy & Hold)', color=BENCH_COLOR, alpha=0.7, ls='--', lw=1.5)
    ax1.set_title('1. Cumulative Returns (Log Scale)', fontsize=11, fontweight='bold', color='#333')
    ax1.set_yscale('log')
    ax1.set_ylabel('Equity ($)')
    ax1.legend(loc='upper left', frameon=True, facecolor='white', framealpha=0.8)
    ax1.grid(True, which='both', alpha=0.2, color='#999')
    
    # --- Panel 2: Drawdown ---
    strat_dd = (df['strategy_equity'] / df['strategy_equity'].cummax()) - 1
    bench_dd = (df['benchmark_equity'] / df['benchmark_equity'].cummax()) - 1
    ax2.fill_between(df.index, strat_dd, 0, color=STRAT_COLOR, alpha=0.2, label='Strategy Drawdown')
    ax2.plot(df.index, bench_dd, color='gray', alpha=0.5, lw=1, label='Benchmark Drawdown')
    ax2.set_title('2. Drawdown Profile (%)', fontsize=11, fontweight='bold', color='#333')
    ax2.set_ylabel('Depth')
    ax2.legend(loc='lower left', frameon=True, facecolor='white', framealpha=0.8)
    ax2.grid(True, alpha=0.2, color='#999')

    # --- Panel 3: Volatility Regime ---
    ax3.plot(df.index, rolling_bench_vol, label='Benchmark Vol', color='gray', alpha=0.4, lw=1)
    ax3.plot(df.index, rolling_strat_vol, label='Strategy Vol', color=VOL_COLOR, lw=1.5)
    ax3.axhline(TARGET_VOL, color='green', ls='--', alpha=0.8, label=f'Target Vol ({TARGET_VOL:.0%})')
    ax3.set_title('3. Volatility Regime (20-day Rolling)', fontsize=11, fontweight='bold', color='#333')
    ax3.set_ylabel('Ann. Volatility')
    ax3.legend(loc='upper left', frameon=True, facecolor='white', framealpha=0.8)
    ax3.grid(True, alpha=0.2, color='#999')
    
    # --- Panel 4: Leverage & Risk Control ---
    ax4.plot(df.index, df['leverage'], label='Leverage Used', color='#1f77b4', lw=1.5)
    ax4.axhline(1.0, color='black', ls=':', alpha=0.5)
    
    # Mark SMA Bear Market Filter (Gray Background)
    if 'sma' in df.columns:
        bear_mask = df['Close'] < df['sma']
        if bear_mask.any():
            import matplotlib.transforms as mtransforms
            labeled = False
            for start, end in _contiguous_regions(bear_mask):
                if not labeled:
                    ax4.axvspan(df.index[start], df.index[end], color='gray', alpha=0.15, label='Bear Filter (SMA)')
                    labeled = True
                else:
                    ax4.axvspan(df.index[start], df.index[end], color='gray', alpha=0.15)

    ax4.set_title('4. Leverage & Risk Controls', fontsize=11, fontweight='bold', color='#333')
    ax4.set_ylabel('Exposure')
    ax4.set_xlabel('Date', fontweight='bold')
    ax4.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.8)
    ax4.grid(True, alpha=0.2, color='#999')
    
    plt.tight_layout()
    
    output_path = os.path.join(output_dir, filename)
    # transparent=True ensures the chart background blends with HTML
    plt.savefig(output_path, dpi=120, bbox_inches='tight', transparent=True)
    plt.close(fig)
    print(f"Chart saved to: {output_path}")
    return output_path

def _contiguous_regions(condition):
    """
    Helper: Find contiguous True regions in a boolean array.
    Used for plotting background shading (e.g., Bear Market regimes).
    """
    d = np.diff(np.concatenate(([False], condition, [False])).astype(int))
    starts = np.where(d == 1)[0]
    ends = np.where(d == -1)[0] - 1
    return zip(starts, ends)