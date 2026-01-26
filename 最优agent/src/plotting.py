import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mdates
import numpy as np

def plot_equity_curve(equity_df: pd.DataFrame, benchmark_df: pd.DataFrame, outpath: str) -> None:
    """
    Plots:
    1. Linear Equity Curve
    2. Log Equity Curve (Saved separately)
    3. Rolling Volatility Analysis (Saved separately)
    """
    # Ensure Datetime Index
    equity_df.index = pd.to_datetime(equity_df.index)
    benchmark_df.index = pd.to_datetime(benchmark_df.index)

    # Align Data Dates
    common_idx = equity_df.index.intersection(benchmark_df.index)
    strat = equity_df.loc[common_idx, "equity"]
    
    # Normalize Benchmark
    bench_price = benchmark_df.loc[common_idx, "Close"]
    bench_equity = (bench_price / bench_price.iloc[0]) * strat.iloc[0]

    # Drawdown
    running_max = strat.cummax()
    drawdown = (strat / running_max) - 1

    # --- Plot 1: Linear Scale ---
    _create_chart(strat, bench_equity, drawdown, outpath, log_scale=False)
    
    # --- Plot 2: Log Scale ---
    log_outpath = outpath.replace(".png", "_log.png")
    _create_chart(strat, bench_equity, drawdown, log_outpath, log_scale=True)
    
    # --- Plot 3: Rolling Volatility (New!) ---
    vol_outpath = outpath.replace("equity_curve.png", "rolling_vol.png")
    _plot_rolling_vol(equity_df, benchmark_df, vol_outpath)
    
    print(f"Charts saved: \n- {outpath}\n- {log_outpath}\n- {vol_outpath}")

def _create_chart(strat, bench_equity, drawdown, path, log_scale=False):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
    
    ax1.plot(strat.index, strat, label="AI Agent Strategy", color="#1f77b4", linewidth=1.5)
    ax1.plot(bench_equity.index, bench_equity, label="Buy & Hold (Benchmark)", color="gray", linestyle="--", alpha=0.6)
    
    title = "Strategy vs Benchmark"
    if log_scale:
        ax1.set_yscale('log')
        title += " (Log Scale)"
        
    ax1.set_title(title, fontsize=14, fontweight="bold")
    ax1.set_ylabel("Equity ($)", fontsize=10)
    ax1.legend(loc="upper left")
    ax1.grid(True, which="both", linestyle="--", alpha=0.3)

    ax2.fill_between(drawdown.index, drawdown, 0, color="red", alpha=0.3)
    ax2.plot(drawdown.index, drawdown, color="red", linewidth=0.8)
    ax2.set_title("Drawdown", fontsize=10, fontweight="bold")
    ax2.set_ylabel("DD %", fontsize=10)
    ax2.set_xlabel("Date", fontsize=10)
    ax2.grid(True, which="both", linestyle="--", alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.close()

def _plot_rolling_vol(equity_df, benchmark_df, path):
    """Plots the Strategy's Realized Volatility vs Benchmark Volatility."""
    # Compute Benchmark Rolling Vol (60 days)
    bench_ret = benchmark_df["Close"].pct_change().fillna(0)
    bench_vol = bench_ret.rolling(60).std() * np.sqrt(252)
    
    # Get Strategy Vol (Already computed in backtest)
    strat_vol = equity_df["strategy_realized_vol"] # This is what the algo saw
    
    # Align
    common_idx = strat_vol.index.intersection(bench_vol.index)
    
    plt.figure(figsize=(12, 6))
    plt.plot(common_idx, bench_vol.loc[common_idx], label="Benchmark Volatility (AMZN)", color="gray", alpha=0.5)
    plt.plot(common_idx, strat_vol.loc[common_idx], label="Strategy Volatility", color="#d62728", linewidth=1.5)
    
    # Draw Target Line (approximate, since target is in config, let's assume 0.20 based on latest)
    plt.axhline(y=0.20, color="green", linestyle="--", label="Target Vol (20%)")
    
    plt.title("Risk Control: Rolling Volatility (60-day)", fontsize=14, fontweight="bold")
    plt.ylabel("Annualized Volatility", fontsize=12)
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.3)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.close()