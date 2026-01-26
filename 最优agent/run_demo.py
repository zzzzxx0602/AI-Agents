import argparse
import json
import os
import pandas as pd

from src.config import AgentConfig
from src.data import download_ohlcv, validate_ohlcv, load_ohlcv_from_csv
from src.strategy import build_features, generate_signals
from src.backtest import backtest_long_only_chandelier_strategy_voltarget
from src.plotting import plot_equity_curve
from src.report import build_trade_note_markdown, build_trade_note_html, try_generate_llm_commentary

def format_metrics_for_llm(metrics: dict) -> dict:
    formatted = metrics.copy()
    pct_keys = ["CAGR", "AnnVol", "MaxDrawdown", "WinRate", "Benchmark_CAGR", "TotalReturn", "Benchmark_TotalReturn"]
    for k in pct_keys:
        if k in formatted and formatted[k] is not None:
            formatted[k] = f"{formatted[k]*100:.2f}%"
    
    num_keys = ["Sharpe", "Sortino", "Calmar", "AvgLeverageMult"]
    for k in num_keys:
        if k in formatted and formatted[k] is not None:
            formatted[k] = f"{formatted[k]:.2f}"
    return formatted

def main():
    #os.environ["OPENAI_API_KEY"] = "Insert your API key..." 

    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=str, default=None, help="Path to OHLCV CSV file (optional)")
    args, unknown = parser.parse_known_args()

    cfg = AgentConfig()
    print(f"--- Starting Technical Agent for {cfg.ticker} ---")

    if args.csv:
        raw = load_ohlcv_from_csv(args.csv)
    else:
        raw = download_ohlcv(cfg.ticker, cfg.start, cfg.end)

    df = validate_ohlcv(raw)
    feat = build_features(df=df, atr_period=cfg.atr_period, st_mult=cfg.supertrend_multiplier, chandelier_lookback=cfg.chandelier_lookback, chandelier_k=cfg.chandelier_k)
    sig = generate_signals(feat, enable_reentry=cfg.enable_reentry)

    print("Running backtest...")
    equity_df, trades_df, metrics = backtest_long_only_chandelier_strategy_voltarget(
        df=sig, initial_equity=cfg.initial_equity, risk_pct_equity=cfg.risk_pct_equity,
        hard_stop_atr_multiple=cfg.hard_stop_atr_multiple, use_trailing_stop=cfg.use_trailing_stop,
        target_ann_vol=cfg.target_ann_vol, strategy_vol_lookback=cfg.strategy_vol_lookback,
        max_leverage=cfg.max_leverage, min_leverage=cfg.min_leverage,
        commission_bps=cfg.commission_bps, slippage_bps=cfg.slippage_bps,
        allow_reentry_same_day=cfg.allow_reentry_same_day, min_atr=cfg.min_atr
    )

    if not os.path.exists("reports"): os.makedirs("reports")
    trades_df.to_csv("reports/trades.csv", index=False)
    equity_df.to_csv("reports/equity_curve.csv")
    plot_equity_curve(equity_df, df, "reports/equity_curve.png")

    latest = sig.iloc[-1]
    last_signal = "Bullish" if latest["ST_Dir"] == 1 else "Bearish"
    last_signal += f" (Chandelier={latest['ChandelierStop']:.2f})"
    
    # [CRITICAL FIX] Added "LONG-ONLY" constraint to the Prompt
    llm_prompt = f"""
    Act as a Senior Hedge Fund Manager. Review this backtest for {cfg.ticker}.
    
    IMPORTANT CONTEXT: This is a **LONG-ONLY** strategy. Short selling is NOT allowed.
    If the signal is Bearish, the only valid action is to **Exit/Hold Cash**. Do NOT recommend shorting.
    
    Metrics: {json.dumps(format_metrics_for_llm(metrics), indent=2)}
    Current Signal: {last_signal} Price: {latest['Close']:.2f}
    
    Write a commentary (approx 250 words) using **Bullet Points**.
    
    Structure your response exactly as follows:
    
    1. **Performance Efficiency**:
       - Compare Strategy CAGR vs Benchmark. 
       - Comment on Sharpe/Sortino ratios.
    
    2. **Market Risk Analysis**:
       - Analyze *current* market risks (e.g., trend exhaustion, volatility regime) relevant to a {last_signal} signal.
       - Focus on external factors (Macro, Momentum).
    
    3. **Actionable Investment Strategy**:
       - Explicitly state the recommendation: **Buy** or **Hold Cash** (NO Shorting).
       - Provide specific technical triggers to watch (e.g., "Wait for price to close above Supertrend resistance").
       - Suggest a mindset for the trader (e.g., "Patience is key").
    """
    
    print("Generating AI Commentary...")
    llm_text = try_generate_llm_commentary(llm_prompt)

    note_md = build_trade_note_markdown(cfg.ticker, cfg.__dict__, metrics, last_signal, str(sig.index[-1].date()), llm_text)
    with open("reports/trade_note.md", "w", encoding="utf-8") as f: f.write(note_md)

    note_html = build_trade_note_html(
        cfg.ticker, cfg.__dict__, metrics, last_signal, str(sig.index[-1].date()), 
        {"equity": "reports/equity_curve_log.png", "vol": "reports/rolling_vol.png"}, llm_text
    )
    with open("reports/trade_note.html", "w", encoding="utf-8") as f: f.write(note_html)

    print("=== Demo Complete ===")
    print(f"Markdown Report: reports/trade_note.md")
    print(f"HTML Report:     reports/trade_note.html")
    
    print("\n" + "="*40)
    print("FINAL STRATEGY METRICS")
    print("="*40)
    formatted = format_metrics_for_llm(metrics)
    disp_order = ["TotalReturn", "CAGR", "Benchmark_CAGR", "Sharpe", "Sortino", "Calmar", "MaxDrawdown", "WinRate"]
    for k in disp_order:
        print(f"{k:<20} : {formatted.get(k, 'N/A')}")
    print("="*40 + "\n")

if __name__ == "__main__":
    main()