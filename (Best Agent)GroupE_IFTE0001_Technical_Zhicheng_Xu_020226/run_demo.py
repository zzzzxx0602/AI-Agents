# run_demo.py
import sys
import os

# Ensure src path is visible
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data import fetch_data
from backtest import run_backtest
from report import save_reports, generate_ai_prompt, query_llm, save_trades_html
from plotting import plot_results
import config 

def main():
    os.environ["OPENAI_API_KEY"] 
    
    ticker = config.TICKER
    print(f"--- Starting Volatility Agent for {ticker} ---")
    
    # 1. Fetch Data
    try:
        df = fetch_data(ticker, config.START_DATE, config.END_DATE)
    except Exception as e:
        print(f"Data Error: {e}")
        return

    # 2. Run Backtest
    print(f"Running backtest...")
    df_res, metrics, trades_df = run_backtest(df)
    metrics['ticker'] = ticker
    
    # 3. Generate Charts
    print("Generating charts...")
    chart_path = plot_results(df_res, output_dir="reports", filename="backtest_chart.png")
    
    # 4. Generate AI Analysis
    print("Generating AI analysis...")
    prompt = generate_ai_prompt(ticker, metrics, df_res.iloc[-1], config)
    ai_response = query_llm(prompt)
    
    # 5. Save Strategy Reports (Trade Note)
    print("Saving strategy reports...")
    save_reports(df_res, metrics, ai_response, config, folder="reports", chart_path=chart_path)
    
    # 6. Save Detailed Trades Log (HTML Table) - NEW!
    print("Saving trades log table...")
    save_trades_html(trades_df, folder="reports", filename="trades_log.html")

    print("\n=== Demo Complete ===")
    print(f"Reports generated in 'reports/':")
    print(f" - trade_note.html (Strategy Overview)")
    print(f" - trades_log.html (Detailed Trades Table)")

if __name__ == "__main__":
    main()