import matplotlib.pyplot as plt
import pandas as pd
import os

def plot_performance_dashboard(df, output_dir="reports"):
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    
    # Color Palette (Navy/Grey Theme)
    COLOR_STRAT = "#1F618D"  # Main Strategy Blue
    COLOR_BENCH = "#95A5A6"  # Benchmark Grey
    COLOR_DD    = "#C0392B"  # Drawdown Red
    COLOR_VOL   = "#34495E"  # Dark Slate (Unified with Text)
    COLOR_LEV   = "#1F618D"  # Re-using Strategy Blue for Leverage (Unified)
    
    plt.rcParams.update({'font.size': 8, 'font.family': 'sans-serif'}) # Smaller font
    
    # --- Chart 1: Equity Curve (More Compact) ---
    fig1, ax1 = plt.subplots(figsize=(8, 2.5)) # Reduced height
    ax1.plot(df['Date'], df['strategy_equity'], label='Enhanced Turtle', color=COLOR_STRAT, linewidth=1.2)
    ax1.plot(df['Date'], df['benchmark_equity'], label='Benchmark', color=COLOR_BENCH, alpha=0.6, linestyle='--', linewidth=1)
    ax1.set_yscale('log')
    ax1.set_title("Equity Growth (Log Scale)", fontweight='bold', pad=8, color='#34495e', fontsize=10)
    ax1.legend(loc='upper left', frameon=False, fontsize=8)
    ax1.grid(True, alpha=0.15)
    ax1.set_ylabel("Multiple", fontsize=8)
    
    chart1_path = os.path.join(output_dir, "equity_chart.png")
    plt.tight_layout()
    plt.savefig(chart1_path, bbox_inches='tight', dpi=150)
    plt.close()

    # --- Chart 2: Comparative Drawdown ---
    fig2, ax2 = plt.subplots(figsize=(8, 2.2)) # Slimmer
    
    dd_bench = (df['benchmark_equity'] / df['benchmark_equity'].cummax()) - 1
    ax2.fill_between(df['Date'], dd_bench, 0, color=COLOR_BENCH, alpha=0.2, label='Benchmark')
    
    dd_strat = (df['strategy_equity'] / df['strategy_equity'].cummax()) - 1
    ax2.fill_between(df['Date'], dd_strat, 0, color=COLOR_DD, alpha=0.6, label='Strategy')
    
    ax2.set_title("Drawdown Risk Profile", fontweight='bold', pad=8, color='#34495e', fontsize=10)
    ax2.legend(loc='lower left', frameon=False, fontsize=8)
    ax2.grid(True, alpha=0.15)
    ax2.set_ylabel("Depth", fontsize=8)
    
    chart2_path = os.path.join(output_dir, "drawdown_chart.png")
    plt.tight_layout()
    plt.savefig(chart2_path, bbox_inches='tight', dpi=150)
    plt.close()

    # --- Chart 3: Volatility Regime ---
    fig3, ax3 = plt.subplots(figsize=(8, 2.2)) # Slimmer
    
    vol_strat = df['strategy_returns'].rolling(20).std() * (252**0.5)
    # Changed color to Dark Slate to match theme
    ax3.plot(df['Date'], vol_strat, color=COLOR_VOL, linewidth=1.0, label='Realized Vol')
    ax3.axhline(0.30, color='#2c3e50', linestyle=':', label='Target (30%)', alpha=0.5)
    
    ax3.set_title("Volatility Control", fontweight='bold', pad=8, color='#34495e', fontsize=10)
    ax3.legend(loc='upper right', frameon=False, fontsize=8)
    ax3.grid(True, alpha=0.15)
    ax3.set_ylabel("Ann. Vol", fontsize=8)
    
    chart3_path = os.path.join(output_dir, "vol_chart.png")
    plt.tight_layout()
    plt.savefig(chart3_path, bbox_inches='tight', dpi=150)
    plt.close()

    # --- Chart 4: Leverage & Exposure  ---
    fig4, ax4 = plt.subplots(figsize=(8, 2.2)) # Slimmer
    
    # Changed color to Strategy Blue 
    ax4.plot(df['Date'], df['leverage'], color=COLOR_LEV, linewidth=1.0, label='Leverage')
    ax4.fill_between(df['Date'], df['leverage'], 0, color=COLOR_LEV, alpha=0.1)
    
    ax4.set_title("Active Position Exposure", fontweight='bold', pad=8, color='#34495e', fontsize=10)
    ax4.set_ylabel("Lev (x)", fontsize=8)
    ax4.grid(True, alpha=0.15)
    
    chart4_path = os.path.join(output_dir, "leverage_chart.png")
    plt.tight_layout()
    plt.savefig(chart4_path, bbox_inches='tight', dpi=150)
    plt.close()

    return chart1_path, chart2_path, chart3_path, chart4_path