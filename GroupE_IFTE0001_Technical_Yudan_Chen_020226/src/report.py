import os
import pandas as pd
import base64
import re

def get_img_tag(path):
    if path and os.path.exists(path):
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')
            return f'<div style="text-align:center; margin: 15px 0;"><img src="data:image/png;base64,{encoded}" style="max-width:100%; width:700px; border-radius:4px; border:1px solid #eee;"></div>'
    return ""

def clean_html_for_md(html_text):
    """
    Cleans HTML tags AND entities for Markdown.
    [MODIFIED] Added replacement for &bull; and other common entities.
    """
    text = re.sub('<[^<]+?>', '', html_text)  # Remove tags
    text = text.replace("&bull;", "-")         # Fix bullet points
    text = text.replace("&nbsp;", " ")         # Fix spaces
    return text.strip()

def save_reports(df, metrics, ai_commentary, config, path1, path2, path3, path4):
    if not os.path.exists("reports"): os.makedirs("reports")
    
    # CSV Log
    df['pos_change'] = df['leverage'].diff().abs()
    trades = df[df['pos_change'] > 0.05].copy()
    trades.to_csv("reports/trades.csv", columns=['Date', 'Close', 'leverage'], index=False)

    # Performance Text Logic
    strat_sharpe = metrics['strat_sharpe']
    bench_sharpe = metrics['bh_sharpe']
    if strat_sharpe > bench_sharpe:
        perf_text = f"outperforming the benchmark (Sharpe: {bench_sharpe:.2f})"
    else:
        perf_text = f"delivering defensive risk-adjusted returns (Sharpe: {strat_sharpe:.2f})"
        
    curr_lev = df['leverage'].iloc[-1]
    curr_price = df['Close'].iloc[-1]
    
    if curr_lev > 0:
        regime_status = "BULLISH TREND"
        regime_color = "#27ae60" 
        stop_level = df['lower_10'].iloc[-1] if 'lower_10' in df.columns else curr_price * 0.95
        advice_body = f"Price Action is constructive. <strong>Maintain Long Position</strong> at {curr_lev:.2f}x leverage. <br>Strictly honor Trailing Stop at <strong>${stop_level:.2f}</strong>."
    else:
        regime_status = "DEFENSIVE / CASH"
        regime_color = "#7f8c8d" 
        entry_level = df['upper_20'].iloc[-1] if 'upper_20' in df.columns else curr_price * 1.05
        advice_body = f"Market is below trend filters. <strong>Hold Cash</strong> (Yielding {config.RISK_FREE_RATE:.1%}). <br>Wait for confirmed breakout above <strong>${entry_level:.2f}</strong>."

    # --- HTML Content ---
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Investment Memo: {config.TICKER}</title>
        <style>
            body {{ font-family: 'Helvetica Neue', Arial, sans-serif; background: #f0f2f5; color: #333; margin: 0; padding: 40px; line-height: 1.5; }}
            .paper {{ background: white; max-width: 850px; margin: auto; padding: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); border-top: 5px solid #2c3e50; }}
            h1 {{ color: #2c3e50; font-size: 26px; border-bottom: 2px solid #eee; padding-bottom: 15px; margin-bottom: 5px; }}
            .meta {{ color: #999; font-size: 13px; margin-bottom: 30px; }}
            h2 {{ color: #2980b9; font-size: 18px; margin-top: 30px; border-left: 4px solid #2980b9; padding-left: 12px; }}
            h3 {{ font-size: 15px; font-weight: bold; margin-top: 15px; color: #34495e; }}
            .exec-summary {{ background: #f8f9fa; padding: 15px; border-radius: 4px; border: 1px solid #e9ecef; margin-bottom: 20px; font-size: 14px; }}
            .advice-box {{ background: {regime_color}15; border-left: 5px solid {regime_color}; padding: 15px; margin: 20px 0; }}
            .metrics-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; }}
            .metrics-table th {{ text-align: left; color: #95a5a6; border-bottom: 1px solid #eee; padding: 8px; }}
            .metrics-table td {{ padding: 10px 8px; border-bottom: 1px solid #f9f9f9; font-weight: 500; }}
            .val-good {{ color: #27ae60; }} .val-bad {{ color: #c0392b; }}
            .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; font-size: 13px; }}
            ul {{ margin: 5px 0; padding-left: 20px; color: #555; }}
            .ai-commentary {{ font-size: 14px; text-align: justify; }}
            .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #bdc3c7; font-size: 10px; }}
        </style>
    </head>
    <body>
        <div class="paper">
            <h1>Trade Note: {config.TICKER}</h1>
            <div class="meta">Date: {pd.Timestamp.now().strftime('%Y-%m-%d')} | Strategy: {config.STRATEGY_NAME}</div>

            <h3>Executive Summary</h3>
            <div class="exec-summary">
                The strategy is currently in a <strong>{regime_status}</strong> regime. 
                Over the backtest period, it generated a CAGR of <strong>{metrics['strat_cagr']:.2%}</strong>, {perf_text}. 
                The model relies on a pure 20-Day Donchian Breakout logic for maximum reactivity, filtered by a macro SMA-200 trend detector.
            </div>

            <div class="advice-box">
                <div style="font-weight:bold; color:{regime_color}; font-size:11px; text-transform:uppercase;">Current Investment Advice</div>
                <div style="font-size:15px; color:#2c3e50;">{advice_body}</div>
            </div>

            <h2>1. Performance Metrics</h2>
            <table class="metrics-table">
                <thead><tr><th>Metric</th><th>Strategy</th><th>Benchmark</th><th>Delta</th></tr></thead>
                <tbody>
                    <tr><td>CAGR</td><td>{metrics['strat_cagr']:.2%}</td><td>{metrics['bh_cagr']:.2%}</td><td class="{ 'val-good' if metrics['strat_cagr'] > metrics['bh_cagr'] else 'val-bad' }">{metrics['strat_cagr'] - metrics['bh_cagr']:+.2%}</td></tr>
                    <tr><td>Sharpe Ratio</td><td>{metrics['strat_sharpe']:.2f}</td><td>{metrics['bh_sharpe']:.2f}</td><td class="{ 'val-good' if metrics['strat_sharpe'] > metrics['bh_sharpe'] else 'val-bad' }">{metrics['strat_sharpe'] - metrics['bh_sharpe']:+.2f}</td></tr>
                    <tr><td>Max Drawdown</td><td class="val-bad">{metrics['strat_max_dd']:.2%}</td><td class="val-bad">{metrics['bh_max_dd']:.2%}</td><td class="{ 'val-good' if metrics['strat_max_dd'] > metrics['bh_max_dd'] else 'val-bad' }">Impr. {metrics['strat_max_dd'] - metrics['bh_max_dd']:+.2%}</td></tr>
                     <tr><td>Hit Rate</td><td>{metrics['hit_rate']:.1%}</td><td>--</td><td>--</td></tr>
                </tbody>
            </table>

            <h2>2. System Architecture</h2>
            <div class="grid-2">
                <div>
                    <h3>Strategy Configuration</h3>
                    <ul>
                        <li><strong>Trend Filter:</strong> Price > SMA(200)</li>
                        <li><strong>Entry Logic:</strong> 20-Day Donchian Breakout</li>
                        <li><strong>Exit Logic:</strong> 10-Day Donchian Breakdown</li>
                        <li><strong>Positioning:</strong> Vol-Targeting ({config.VOL_TARGET:.0%})</li>
                        <li><strong>Cost Model:</strong> {config.RISK_FREE_RATE:.1%} Financing</li>
                    </ul>
                </div>
                <div>
                    <h3>Structural Risks</h3>
                    <ul>
                        <li><strong>Whipsaw Decay:</strong> Sideways markets trigger false breakouts.</li>
                        <li><strong>Gap Risk:</strong> Overnight volatility skips stops.</li>
                        <li><strong>Execution Lag:</strong> T+1 entry pricing.</li>
                    </ul>
                </div>
            </div>

            <h2>3. AI Analyst Commentary</h2>
            <div class="ai-commentary">{ai_commentary}</div>

            <h2>4. Visual Evidence</h2>
            {get_img_tag(path1)}
            {get_img_tag(path2)}
            {get_img_tag(path3)}
            {get_img_tag(path4)}
            
            <div style="margin-top:20px; padding-top:10px; border-top:1px solid #eee; font-size:10px; color:#999;">
                <strong>DISCLAIMER:</strong> This report is generated by an autonomous AI agent for educational purposes (MSc Coursework). 
                It does not constitute financial advice. The strategy utilizes leverage which amplifies risks. 
                Past performance is not indicative of future results.
            </div>

            <div class="footer">
                Strategy: {config.STRATEGY_NAME} | Financing Cost: {config.RISK_FREE_RATE:.1%} | Transaction Cost: {config.COST_BPS}bps
            </div>
        </div>
    </body>
    </html>
    """
    with open("reports/trade_note.html", "w") as f:
        f.write(html_content)
    
    # --- MARKDOWN SYNC  ---
    md_content = f"""# Trade Note: {config.TICKER}
**Strategy:** {config.STRATEGY_NAME} | **Date:** {pd.Timestamp.now().strftime('%Y-%m-%d')}

## 1. Executive Summary
The strategy is currently in a **{regime_status}** regime.
Over the backtest period, it generated a CAGR of **{metrics['strat_cagr']:.2%}**. The model relies on a pure 20-Day Donchian Breakout logic for maximum reactivity.

## 2. Current Investment Advice
{clean_html_for_md(advice_body)}

## 3. Performance Metrics
| Metric | Strategy | Benchmark | Delta |
| :--- | :--- | :--- | :--- |
| **CAGR** | {metrics['strat_cagr']:.2%} | {metrics['bh_cagr']:.2%} | {metrics['strat_cagr'] - metrics['bh_cagr']:+.2%} |
| **Sharpe** | {metrics['strat_sharpe']:.2f} | {metrics['bh_sharpe']:.2f} | {metrics['strat_sharpe'] - metrics['bh_sharpe']:+.2f} |
| **Max DD** | {metrics['strat_max_dd']:.2%} | {metrics['bh_max_dd']:.2%} | {metrics['strat_max_dd'] - metrics['bh_max_dd']:+.2%} |
| **Hit Rate** | {metrics['hit_rate']:.1%} | -- | -- |

## 4. System Architecture
### Configuration
- **Trend Filter:** Price > SMA(200)
- **Entry:** 20-Day Breakout
- **Exit:** 10-Day Breakdown
- **Vol Target:** {config.VOL_TARGET:.0%}

### Structural Risks
- Whipsaw Decay (False Breakouts)
- Overnight Gap Risk
- Financing Drag (4% Cost)

## 5. AI Analyst Commentary
{clean_html_for_md(ai_commentary)}

*(See HTML report for Charts)*
"""
    with open("reports/trade_note.md", "w") as f:
        f.write(md_content)

    print("Reports generated: reports/trade_note.html & trade_note.md")