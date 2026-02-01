import os
import sys
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import config
from data import fetch_data
from strategy import TurtleAgent
from backtest import run_backtest
from plotting import plot_performance_dashboard
from report import save_reports

def query_llm_professional(metrics, config, last_row):
    """
    Generates professional commentary.
    [FIXED] Now dynamically adjusts advice based on current leverage to match the Trade Note.
    """
    curr_lev = last_row['leverage']
    
    # Dynamic logic for the Outlook section
    if curr_lev > 0:
        outlook_html = f"""
        The system currently detects a constructive technical setup (Price > SMA-200). 
        Exposure is active at <b>{curr_lev:.2f}x leverage</b>. 
        The directive is to <b>Maintain Long</b>, prioritizing the 10-day trailing stop to lock in momentum.
        """
    else:
        outlook_html = f"""
        The system identifies a defensive regime (Price < Trend Filter or recent Breakdown). 
        Exposure has been cut to <b>0.00x (Cash)</b> to preserve capital. 
        The directive is to <b>Remain Defensive</b> and await a confirmed breakout above the 20-day high.
        """

    return f"""
    <p><b>&bull; Performance Verdict (Momentum Focused):</b><br>
    The Enhanced Turtle strategy prioritizes speed over complexity. 
    By utilizing a pure <b>20-Day Breakout</b> logic without lagging filters, the system captures high-velocity trends early. 
    This approach generated a CAGR of <b>{metrics['strat_cagr']:.2%}</b>, validating the thesis that reacting to price action is superior to predicting it.</p>

    <p><b>&bull; Risk-Adjusted Mechanics:</b><br>
    Despite the aggressive entry logic, downside risk is rigorously managed. The <b>SMA-200 Regime Filter</b> acts as a macro circuit breaker, while the <b>Volatility Targeting</b> engine dynamically adjusted sizing throughout the backtest. 
    This dual-layer defense limited the Max Drawdown to <b>{metrics['strat_max_dd']:.2%}</b> (vs Benchmark {metrics['bh_max_dd']:.2%}).</p>

    <p><b>&bull; Forward Outlook:</b><br>
    {outlook_html}</p>
    """

def main():
    #os.environ["OPENAI_API_KEY"] = "sk..." 
    print(f"--- Starting {config.STRATEGY_NAME} ---")
    
    # 1. Data
    try:
        df = fetch_data(config.TICKER, config.START_DATE)
    except Exception as e:
        print(f"Data Error: {e}"); return

    # 2. Strategy
    agent = TurtleAgent(df)
    df_signaled = agent.generate_signals(config)
    
    # 3. Backtest
    df_res, metrics = run_backtest(df_signaled, config)
    
    # 4. Plots
    c1, c2, c3, c4 = plot_performance_dashboard(df_res, output_dir="reports")
    
    # 5. Report
    ai_commentary = query_llm_professional(metrics, config, df_res.iloc[-1])
    save_reports(df_res, metrics, ai_commentary, config, c1, c2, c3, c4)
    
    print("-" * 30)
    print(f"Strategy: {config.STRATEGY_NAME}")
    print(f"Final CAGR: {metrics['strat_cagr']:.2%}")
    print("Report Generation Complete.")

if __name__ == "__main__":
    main()