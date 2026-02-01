# src/report.py
import os
import base64
import pandas as pd

# --- CSS Styling ---
HTML_CSS = """
<style>
    body { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 1200px; margin: 0 auto; padding: 40px; background-color: #f9f9f9; }
    .container { background: #fff; padding: 40px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 30px; }
    h1 { margin-top: 0; color: #2c3e50; font-size: 26px; border-bottom: 2px solid #eaeaea; padding-bottom: 15px; }
    .subtitle { font-size: 16px; color: #7f8c8d; margin-bottom: 30px; }
    h2 { color: #2980b9; font-size: 20px; margin-top: 35px; padding-bottom: 8px; border-bottom: 1px solid #eee; }
    table { width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; }
    th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #f1f1f1; }
    th { background-color: #f8f9fa; font-weight: 600; color: #555; position: sticky; top: 0; }
    .metric-value { font-family: "Menlo", "Consolas", monospace; color: #2c3e50; }
    .description { color: #888; font-size: 13px; font-style: italic; }
    .tag { display: inline-block; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; color: #fff; }
    .tag-green { background-color: #27ae60; }
    .tag-red { background-color: #c0392b; }
    .tag-yellow { background-color: #f39c12; color: #fff; }
    .chart-container { margin-top: 40px; text-align: center; border: 1px solid #eee; padding: 20px; border-radius: 5px; background-color: #fff; }
    .chart-container img { max-width: 85%; height: auto; }
    .ai-box { background-color: #f0f4f8; border-left: 4px solid #2980b9; padding: 20px; margin-top: 20px; border-radius: 4px; }
    .ai-box h3 { margin-top: 0; color: #2980b9; font-size: 18px; }
    .footer { margin-top: 50px; text-align: center; font-size: 12px; color: #aaa; border-top: 1px solid #eee; padding-top: 20px; }
    .pnl-pos { color: #27ae60; font-weight: bold; }
    .pnl-neg { color: #c0392b; font-weight: bold; }
</style>
"""

# --- Helpers ---
def image_to_base64(img_path):
    if not img_path or not os.path.exists(img_path): return None
    with open(img_path, "rb") as f: return base64.b64encode(f.read()).decode("utf-8")

def format_currency(x):
    if pd.isna(x): return ""
    return f"${x:,.2f}"

def color_pnl(val):
    if pd.isna(val): return ""
    css_class = 'pnl-pos' if val >= 0 else 'pnl-neg'
    return f'<span class="{css_class}">{format_currency(val)}</span>'

# --- AI Functions ---
def generate_ai_prompt(ticker, metrics, latest_data, config):
    date_str = latest_data.name.strftime('%Y-%m-%d')
    price = latest_data['Close']
    sma = latest_data.get('sma', 0)
    rsi = latest_data.get('rsi', 50)
    lev = latest_data.get('leverage', 0)
    trend = "BULLISH" if price > sma else "BEARISH"
    mom = "OVERBOUGHT" if rsi > config.RSI_HIGH else "NEUTRAL"
    
    prompt = f"""
    Act as a Senior Portfolio Manager. Write a trade commentary for the {ticker} strategy (Date: {date_str}).
    
    [Data Context]
    - Strategy CAGR: {metrics['strat_cagr']:.1%} vs Benchmark: {metrics['bh_cagr']:.1%}
    - Sharpe: {metrics['strat_sharpe']:.2f}
    - Signal: {trend} (Price {price:.2f} vs SMA {sma:.2f})
    - RSI: {rsi:.1f} ({mom})
    - Leverage: {lev:.2f}x
    
    [Format]
    1. **Strategy Efficiency**: Compare CAGR/Sharpe.
    2. **Market Risk Analysis**: Analyze Technicals & Volatility.
    3. **Actionable Investment Strategy**: "Maintain" or "Cash" recommendation.
    
    Keep it professional, < 200 words.
    """
    return prompt

def query_llm(prompt):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key: return "<p><em>AI Commentary Unavailable.</em></p>"
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You are a hedge fund analyst. Output HTML paragraphs <p> and <b>."}, {"role": "user", "content": prompt}],
            temperature=0.5
        )
        content = response.choices[0].message.content.strip()
        content = content.replace("**", "<b>").replace("**", "</b>")
        if not content.startswith("<p>"): content = f"<p>{content}</p>"
        return content
    except Exception as e: return f"<p style='color:red'>AI Error: {e}</p>"

# --- REPORT GENERATOR 1: Main Strategy Report ---
def save_reports(df, metrics, ai_commentary, config, folder="reports", chart_path=None):
    if not os.path.exists(folder): os.makedirs(folder)
    last = df.iloc[-1]
    date_str = last.name.strftime('%Y-%m-%d')
    ticker = metrics.get('ticker', 'Unknown')
    
    is_bullish = last['Close'] > last['sma']
    is_overbought = last['rsi'] > config.RSI_HIGH
    
    # Updated text to reflect "10% Buffer"
    if not is_bullish:
        signal_text = f"Bearish (< SMA{config.SMA_WINDOW})"
        action_text = "DEFENSIVE (Cap 1.0x or Cash)"
        action_class = "tag-red"
    elif is_overbought:
        signal_text = f"Bullish but Overbought"
        action_text = "TRIM EXPOSURE"
        action_class = "tag-yellow"
    else:
        signal_text = "Bullish & Stable"
        action_text = "MAINTAIN / ADD RISK"
        action_class = "tag-green"

    chart_html = ""
    if chart_path:
        b64_img = image_to_base64(chart_path)
        if b64_img:
            chart_html = f"""<h2>6) Performance Charts</h2><div class="chart-container"><img src="data:image/png;base64,{b64_img}" alt="Performance"></div>"""

    metrics_rows = [
        ("CAGR", f"{metrics['strat_cagr']:.2%}", f"{metrics['bh_cagr']:.2%}", "Annualized Growth"),
        ("Sharpe Ratio", f"{metrics['strat_sharpe']:.2f}", f"{metrics['bh_sharpe']:.2f}", "Return per unit of Risk"),
        ("Sortino Ratio", f"{metrics['strat_sortino']:.2f}", f"{metrics['bh_sortino']:.2f}", "Downside Risk-Adjusted"),
        ("Calmar Ratio", f"{metrics['strat_calmar']:.2f}", f"{metrics['bh_calmar']:.2f}", "Return / Max Drawdown"),
        ("Max Drawdown", f"{metrics['strat_max_dd']:.2%}", f"{metrics['bh_max_dd']:.2%}", "Deepest Decline"),
        ("Hit Rate", f"{metrics.get('win_rate', 0):.2%}", "--", "% of Profitable Days")
    ]
    rows_html = "".join([f"<tr><td>{m[0]}</td><td class='metric-value'>{m[1]}</td><td>{m[2]}</td><td class='description'>{m[3]}</td></tr>" for m in metrics_rows])
    
    # HTML Content
    html_content = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Trade Note - {ticker}</title>{HTML_CSS}</head><body><div class="container"><h1>Trade Note — {ticker} <span style="float:right; font-size: 16px; color: #999; font-weight: normal;">{date_str}</span></h1><div class="subtitle">Strategy: Trend-Aware Volatility Targeting</div><h2>1) Executive Summary</h2><ul><li><strong>Signal Regime:</strong> {signal_text} | Realized Vol: <strong>{last['rolling_vol']:.1%}</strong></li><li><strong>Action Required:</strong> <span class="tag {action_class}">{action_text}</span></li><li><strong>Current Position:</strong> {metrics['final_leverage']:.2f}x Leverage</li></ul><h2>2) Key Metrics (vs Benchmark)</h2><table><thead><tr><th>Metric</th><th>Strategy</th><th>Benchmark</th><th>Description</th></tr></thead><tbody>{rows_html}</tbody></table><h2>3) Strategy Configuration</h2><ul><li><strong>Entry Signal:</strong> Volatility Targeting (Target {config.TARGET_VOL:.0%})</li><li><strong>Trend Filter:</strong> SMA({config.SMA_WINDOW}) (with 10% Exit Buffer)</li><li><strong>Momentum Filter:</strong> RSI({config.RSI_WINDOW}) > {config.RSI_HIGH}</li><li><strong>Constraints:</strong> Max Leverage {config.MAX_LEVERAGE}x | Rebalance Threshold {config.REBALANCE_THRESHOLD:.0%}</li><li><strong>Financing:</strong> Risk-Free Rate {config.RISK_FREE_RATE:.0%} | Cost {config.COST_BPS}bps</li></ul><h2>4) Structural Risks</h2><ul><li><strong>Signal Whipsaw:</strong> Frequent regime changes in sideways markets.</li><li><strong>Lag Risk:</strong> 20-day vol lookback may delay crash reaction.</li><li><strong>Cost Drag:</strong> Financing costs in flat markets.</li></ul><div class="ai-box"><h3>5) AI Analyst Commentary</h3>{ai_commentary}</div>{chart_html}<div class="footer">Generated by AI Quantitative Agent | Not Financial Advice</div></div></body></html>"""
    
    with open(os.path.join(folder, "trade_note.html"), "w", encoding='utf-8') as f: f.write(html_content)
    
    # Markdown Content
    ai_text_md = ai_commentary.replace("<b>", "**").replace("</b>", "**").replace("<p>", "").replace("</p>", "\n\n").strip()
    rows_md = "\n".join([f"| **{m[0]}** | {m[1]} | {m[2]} | {m[3]} |" for m in metrics_rows])
    md_content = f"""# Trade Note — {ticker} ({date_str})
**Strategy:** Trend-Aware Volatility Targeting

## 1) Executive Summary
- **Signal:** {signal_text}
- **Action:** {action_text}
- **Leverage:** {metrics['final_leverage']:.2f}x

## 2) Key Metrics
| Metric | Strategy | Benchmark | Description |
| :--- | :--- | :--- | :--- |
{rows_md}

## 3) Strategy Configuration
- **Entry:** Vol Target {config.TARGET_VOL:.0%}
- **Trend Filter:** SMA({config.SMA_WINDOW}) with 10% Exit Buffer
- **Constraints:** Max Lev {config.MAX_LEVERAGE}x

## 4) Structural Risks
- Signal Whipsaw
- Volatility Lag
- Cost Drag

## 5) AI Commentary
{ai_text_md}
"""
    with open(os.path.join(folder, "trade_note.md"), "w", encoding='utf-8') as f: f.write(md_content)
    print(f"Main Strategy Reports updated in {folder}")

# --- REPORT GENERATOR 2: Detailed Trades Table ---
def save_trades_html(trades_df, folder="reports", filename="trades_log.html"):
    if not os.path.exists(folder): os.makedirs(folder)
    if trades_df is None or trades_df.empty: return

    df_disp = trades_df.copy()
    for col in ['entry_date', 'exit_date']:
        if col in df_disp.columns: df_disp[col] = pd.to_datetime(df_disp[col]).dt.strftime('%Y-%m-%d')
    
    col_map = {'entry_date': 'Entry Date', 'exit_date': 'Exit Date', 'entry_price': 'Entry Price', 'exit_price': 'Exit Price', 'shares': 'Shares', 'leverage_mult_at_entry': 'Lev Mult', 'pnl': 'PnL ($)', 'exit_reason': 'Exit Reason'}
    df_disp = df_disp.rename(columns={k: v for k, v in col_map.items() if k in df_disp.columns})
    
    if 'Entry Price' in df_disp.columns: df_disp['Entry Price'] = df_disp['Entry Price'].apply(format_currency)
    if 'Exit Price' in df_disp.columns: df_disp['Exit Price'] = df_disp['Exit Price'].apply(format_currency)
    if 'Lev Mult' in df_disp.columns: df_disp['Lev Mult'] = df_disp['Lev Mult'].apply(lambda x: f"{x:.2f}x")
    if 'Shares' in df_disp.columns: df_disp['Shares'] = df_disp['Shares'].apply(lambda x: f"{x:,.0f}")
    if 'PnL ($)' in df_disp.columns: df_disp['PnL ($)'] = df_disp['PnL ($)'].apply(color_pnl)

    html_content = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Trade Log</title>{HTML_CSS}</head><body><div class="container"><h1>Holding Periods Log <span style="float:right; font-size: 16px; color: #999; font-weight: normal;">{len(df_disp)} Rounds</span></h1><table>{df_disp.to_html(index=False, escape=False, border=0)}</table><div class="footer">Generated by AI Quantitative Agent</div></div></body></html>"""
    with open(os.path.join(folder, filename), "w", encoding='utf-8') as f: f.write(html_content)
    
    # Save CSV
    trades_df.to_csv(os.path.join(folder, "trades.csv"), index=False)
    print(f"Trades Report generated: {os.path.join(folder, filename)}")

# --- REPORT GENERATOR 3: Daily Transactions ---
def save_daily_transactions_html(df_res, folder="reports", filename="daily_transactions.html"):
    if not os.path.exists(folder): os.makedirs(folder)
    
    trans_df = df_res.copy()
    trans_df['Position_Value'] = trans_df['strategy_equity'] * trans_df['leverage']
    trans_df['Shares'] = trans_df['Position_Value'] / trans_df['Close']
    trans_df['Delta_Shares'] = trans_df['Shares'].diff().fillna(0)
    
    actions = trans_df[abs(trans_df['Delta_Shares']) > 0.1].copy()
    if actions.empty: return

    display_df = pd.DataFrame()
    display_df['Date'] = actions.index.strftime('%Y-%m-%d')
    display_df['Action'] = actions['Delta_Shares'].apply(lambda x: 'BUY' if x > 0 else 'SELL')
    display_df['Shares'] = abs(actions['Delta_Shares']).apply(lambda x: f"{x:,.2f}")
    display_df['Price'] = actions['Close'].apply(format_currency)
    display_df['Value ($)'] = (abs(actions['Delta_Shares']) * actions['Close']).apply(format_currency)
    display_df['New Leverage'] = actions['leverage'].apply(lambda x: f"{x:.2f}x")
    
    def color_action(val):
        color = '#27ae60' if val == 'BUY' else '#c0392b'
        return f'<span style="color: {color}; font-weight:bold;">{val}</span>'
    display_df['Action'] = display_df['Action'].apply(color_action)

    html_content = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Daily Transaction Log</title>{HTML_CSS}</head><body><div class="container"><h1>Daily Transaction Log <span style="float:right; font-size: 16px; color: #999; font-weight: normal;">{len(display_df)} Actions</span></h1><div class="subtitle">Detailed record of daily rebalancing and leverage adjustments.</div><table><thead><tr><th>Date</th><th>Action</th><th>Shares</th><th>Price</th><th>Est. Value</th><th>New Leverage</th></tr></thead><tbody>{display_df.to_html(index=False, escape=False, border=0, header=False)}</tbody></table><div class="footer">Generated by AI Quantitative Agent</div></div></body></html>"""
    with open(os.path.join(folder, filename), "w", encoding='utf-8') as f: f.write(html_content)
    print(f"Daily Transactions Report generated: {os.path.join(folder, filename)}")