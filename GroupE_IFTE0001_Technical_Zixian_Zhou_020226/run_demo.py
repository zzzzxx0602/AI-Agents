import os
from openai import OpenAI
from src.config import Config
from src import data, indicators, strategy, backtest, report, plotting

def main():
    if not os.path.exists("reports"): os.makedirs("reports")

    # 1. Fetch Data
    try:
        df = data.get_data(Config.TICKER, Config.START_DATE, Config.END_DATE)
    except Exception as e:
        print(f"Data Error: {e}")
        return

    # 2. Calculate Indicators & Signals
    try:
        df = indicators.add_indicators(df, Config)
        df = strategy.generate_signals(df)
    except Exception as e:
        print(f"Indicator Error: {e}")
        return
    
    if df.empty:
        print("Error: DataFrame empty after indicators.")
        return
    
    # Get current status
    last_row = df.iloc[-1]
    signal_status = "Bullish (Breakout)" if last_row['Bullish_Condition'] else "Bearish / Neutral"
    last_price = last_row['Close']
    
    # Strategy Name (Professional Naming)
    strategy_display_name = f"Dynamic Trend (EMA {Config.EMA_SHORT})"
    
    print(f"\n--- Running Backtest: {strategy_display_name} ---")
    
    # 3. Run Backtest
    df, trades, strat_metrics = backtest.run_backtest(
        df, 
        initial_capital=Config.INITIAL_CAPITAL,
        commission=Config.COMMISSION,
        slippage=Config.SLIPPAGE,
        trailing_stop_pct=Config.TRAILING_STOP_PCT,
        stop_loss_pct=Config.STOP_LOSS_PCT,
        use_atr=Config.USE_ATR_STOP,
        atr_multiplier=Config.ATR_MULTIPLIER,
        use_vol_target=Config.USE_VOL_TARGET,
        max_leverage=Config.MAX_LEVERAGE
    )
    
    # Save Trade Record
    trades_csv_path = "reports/trades.csv"
    trades.to_csv(trades_csv_path, index=False)
    print(f"Trade record saved to: {trades_csv_path}")
    
    # 4. Calculate Benchmark
    bench_metrics = backtest.calculate_benchmark_metrics(df, Config.INITIAL_CAPITAL)
    
    # 5. Display Console Metrics
    print("\n--- PERFORMANCE METRICS ---")
    for k, v in strat_metrics.items():
        b_val = bench_metrics.get(k)
        
        # Format Strategy Values
        if "Return" in k or "CAGR" in k or "Drawdown" in k or "Rate" in k:
            s_str = f"{v:.2%}"
        else:
            s_str = f"{v:.2f}"
        
        # Format Benchmark Values
        if b_val is not None:
            if "Return" in k or "CAGR" in k or "Drawdown" in k:
                b_str = f"{b_val:.2%}"
            else:
                b_str = f"{b_val:.2f}"
        else:
            b_str = "--"
            
        print(f"{k.ljust(15)}: Strategy={s_str} | Bench={b_str}")
        
    print("\nGenerating charts (Equity, Volatility, Drawdown, Position)...")
    plotting.plot_performance(df, Config.TICKER, Config.INITIAL_CAPITAL)
    
    print("\nGenerating Report...")
    client = None
    if Config.OPENAI_API_KEY.startswith("sk-"):
        client = OpenAI(api_key=Config.OPENAI_API_KEY)
    else:
        print("[Warning] No API Key. Using placeholder text.")
    
    generator = report.ReportGenerator(client, output_dir="reports")
    md, html = generator.generate(
        ticker=Config.TICKER, 
        metrics=strat_metrics, 
        bench_metrics=bench_metrics, 
        config=Config,
        strategy_name=strategy_display_name,
        last_price=last_price,
        signal_status=signal_status
    )
    print(f"Saved: {md}\nSaved: {html}")

if __name__ == "__main__":
    main()
