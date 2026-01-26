import os
import base64
import re
import pandas as pd
from openai import OpenAI

def format_pct(x: float) -> str:
    if x is None or pd.isna(x):
        return "n/a"
    return f"{x*100:.2f}%"

def format_num(x: float) -> str:
    if x is None or pd.isna(x):
        return "n/a"
    return f"{x:,.2f}"

def get_actionable_advice(last_signal: str) -> str:
    if "Bearish" in last_signal:
        return "MAINTAIN CASH / DO NOT ENTER. Wait for bullish confirmation."
    else:
        return "CONSIDER LONG ENTRY. Monitor Stop Loss."

def image_to_base64(img_path: str) -> str:
    if not os.path.exists(img_path):
        return ""
    with open(img_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def markdown_to_html(text: str) -> str:
    if not text: return ""
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'#+\s*(.*?)\n', r'<b>\1</b><br>', text)
    text = text.replace("\n- ", "<br>&bull; ")
    text = text.replace("- ", "&bull; ")
    text = text.replace('\n', '<br>')
    return text

def build_trade_note_markdown(ticker, config_dict, metrics, last_signal, as_of, llm_text=None):
    advice = get_actionable_advice(last_signal)
    
    lines = []
    lines.append(f"# Trade Note — {ticker} ({as_of})")
    lines.append("**Strategy:** Volatility Targeting (Trend Following)")
    lines.append("")
    lines.append("## 1) Executive Summary")
    lines.append(f"- **Signal:** {last_signal}")
    lines.append(f"- **Action:** {advice}")
    lines.append("")
    lines.append("## 2) Key Metrics")
    lines.append("| Metric | Strategy | Benchmark |")
    lines.append("| :--- | :--- | :--- |")
    lines.append(f"| **Total Return** | {format_pct(metrics.get('TotalReturn'))} | {format_pct(metrics.get('Benchmark_TotalReturn'))} |")
    lines.append(f"| **CAGR** | {format_pct(metrics.get('CAGR'))} | {format_pct(metrics.get('Benchmark_CAGR'))} |")
    lines.append(f"| **Sharpe** | {format_num(metrics.get('Sharpe'))} | -- |")
    lines.append(f"| **Max DD** | {format_pct(metrics.get('MaxDrawdown'))} | -- |")
    lines.append("")
    lines.append("## 3) Strategy Configuration")
    lines.append(f"- **Entry:** Supertrend (ATR={config_dict['atr_period']}, Mult={config_dict['supertrend_multiplier']})")
    lines.append(f"- **Exit:** Chandelier (Lookback={config_dict['chandelier_lookback']}, k={config_dict['chandelier_k']})")
    # Compact Risk Management line for Markdown too
    lines.append(f"- **Risk:** Hard Stop {config_dict['hard_stop_atr_multiple']}x ATR | Sizing {config_dict['risk_pct_equity']*100:.1f}% | Vol Target {config_dict['target_ann_vol']*100:.1f}% (Cap {config_dict['max_leverage']}x)")
    
    if llm_text:
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 4) AI Market Analysis")
        lines.append(llm_text.strip())
        
    return "\n".join(lines)

def build_trade_note_html(ticker, config_dict, metrics, last_signal, as_of, charts, llm_text=None):
    advice = get_actionable_advice(last_signal)
    
    is_bearish = "Bearish" in last_signal
    status_color = "#d9534f" if is_bearish else "#5cb85c"
    advice_color = "#fdebd0" if is_bearish else "#d4efdf"
    advice_text_color = "#d35400" if is_bearish else "#186a3b"
    
    img_equity = image_to_base64(charts.get("equity", ""))
    img_vol = image_to_base64(charts.get("vol", ""))
    
    html_parts = []
    
    # CSS Tweaks for Compactness (Two-Page Goal)
    html_parts.append("<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'><style>")
    html_parts.append("body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; background-color: #f4f6f8; color: #333; }")
    html_parts.append(".container { background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }") # Reduced padding
    html_parts.append(".header { border-bottom: 2px solid #eaeaea; padding-bottom: 10px; margin-bottom: 15px; display: flex; justify-content: space-between; }")
    html_parts.append("h1 { margin: 0; color: #2c3e50; font-size: 22px; }") # Smaller H1
    html_parts.append("h2 { color: #2c3e50; border-left: 4px solid #3498db; padding-left: 10px; margin-top: 20px; margin-bottom: 10px; font-size: 16px; }") # Compact H2
    html_parts.append("table { width: 100%; border-collapse: collapse; margin-top: 5px; font-size: 13px; }") # Compact Table
    html_parts.append("th, td { padding: 8px; text-align: left; border-bottom: 1px solid #f0f0f0; }") # Reduced cell padding
    html_parts.append("th { background-color: #fafafa; font-weight: 600; }")
    html_parts.append(f".signal-box {{ padding: 6px 12px; background-color: {status_color}; color: white; border-radius: 4px; font-weight: bold; display: inline-block; font-size: 13px; }}")
    html_parts.append(f".recommendation {{ margin-top: 10px; padding: 10px; background-color: {advice_color}; border-radius: 4px; color: {advice_text_color}; font-weight: bold; border: 1px solid {status_color}; font-size: 13px; }}")
    html_parts.append(".ai-commentary { background-color: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #9b59b6; line-height: 1.5; color: #444; font-size: 13px; }") # Tighter line height
    html_parts.append(".chart-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 10px; }")
    html_parts.append(".chart-item img { width: 100%; border-radius: 4px; border: 1px solid #eee; }")
    html_parts.append(".footer { margin-top: 20px; border-top: 1px solid #ddd; padding-top: 10px; font-size: 10px; color: #999; text-align: center; }")
    html_parts.append(".config-list { font-size: 13px; padding-left: 20px; margin: 0; }")
    html_parts.append(".config-list li { margin-bottom: 4px; }")
    html_parts.append("</style><title>Trade Note</title></head><body>")
    
    # Body
    html_parts.append("<div class='container'><div class='header'>")
    html_parts.append(f"<div><h1>{ticker} Strategy Report</h1><div style='color:#7f8c8d; font-size:12px; margin-top:2px;'>Date: {as_of} | AI Generated</div></div>")
    html_parts.append(f"<div style='text-align:right; font-size:11px; color:#666;'><strong>Model:</strong> Volatility Targeting<br><strong>Asset:</strong> {ticker}</div></div>")

    # 1. Signal
    html_parts.append("<div class='section'><h2>1. Signal & Action</h2>")
    html_parts.append(f"<div class='signal-box'>{last_signal}</div>")
    html_parts.append(f"<div class='recommendation'>ACTION: {advice}</div></div>")

    # 2. Metrics
    html_parts.append("<div class='section'><h2>2. Key Metrics</h2>")
    html_parts.append("<table><thead><tr><th>Metric</th><th>Strategy</th><th>Benchmark</th><th>Notes</th></tr></thead><tbody>")
    html_parts.append(f"<tr><td>Total Return</td><td>{format_pct(metrics.get('TotalReturn'))}</td><td>{format_pct(metrics.get('Benchmark_TotalReturn'))}</td><td>Cumulative</td></tr>")
    html_parts.append(f"<tr><td>CAGR</td><td>{format_pct(metrics.get('CAGR'))}</td><td>{format_pct(metrics.get('Benchmark_CAGR'))}</td><td>Annualized</td></tr>")
    html_parts.append(f"<tr><td>Sharpe Ratio</td><td>{format_num(metrics.get('Sharpe'))}</td><td>--</td><td>Risk-Adjusted</td></tr>")
    html_parts.append(f"<tr><td>Sortino Ratio</td><td>{format_num(metrics.get('Sortino'))}</td><td>--</td><td>Downside Risk</td></tr>")
    html_parts.append(f"<tr><td>Calmar Ratio</td><td>{format_num(metrics.get('Calmar'))}</td><td>--</td><td>Return/MaxDD</td></tr>")
    html_parts.append(f"<tr><td>Max Drawdown</td><td>{format_pct(metrics.get('MaxDrawdown'))}</td><td>--</td><td>Max Loss</td></tr>")
    html_parts.append("</tbody></table></div>")

    # 3. Charts (Moved up to save visual flow, keeping it compact)
    html_parts.append("<div class='section'><h2>3. Performance Visualization</h2>")
    html_parts.append("<div class='chart-grid'>")
    html_parts.append(f"<div class='chart-item'><img src='data:image/png;base64,{img_equity}' alt='Equity'></div>")
    html_parts.append(f"<div class='chart-item'><img src='data:image/png;base64,{img_vol}' alt='Vol'></div>")
    html_parts.append("</div></div>")

    # 4. Config (Compacted)
    html_parts.append("<div class='section'><h2>4. Strategy Configuration</h2>")
    html_parts.append("<ul class='config-list'>")
    html_parts.append(f"<li><strong>Entry Signal:</strong> Supertrend Bullish Flip (ATR={config_dict['atr_period']}, Mult={config_dict['supertrend_multiplier']})</li>")
    html_parts.append(f"<li><strong>Exit Signal:</strong> Chandelier Stop (Trailing) (Lookback={config_dict['chandelier_lookback']}, k={config_dict['chandelier_k']})</li>")
    # [修改点] 将 Risk Management 的三个点合并为一行，使用 span 和颜色区分
    html_parts.append(f"<li><strong>Risk Management:</strong> Hard Stop {config_dict['hard_stop_atr_multiple']}x ATR <span style='color:#ccc'>|</span> Position Sizing {config_dict['risk_pct_equity']*100:.1f}% <span style='color:#ccc'>|</span> Vol Target {config_dict['target_ann_vol']*100:.1f}% (Max {config_dict['max_leverage']}x)</li>")
    html_parts.append("</ul></div>")

    # 5. AI Commentary
    if llm_text:
        clean_html_text = markdown_to_html(llm_text)
        html_parts.append(f"<div class='section'><h2>5. AI Market Analysis</h2><div class='ai-commentary'>{clean_html_text}</div></div>")

    html_parts.append("<div class='footer'>Disclaimer: Educational purpose only. Not financial advice.</div></div></body></html>")
    
    return "".join(html_parts)

def try_generate_llm_commentary(prompt: str) -> str | None:
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Check if API key exists
    if not api_key:
        print("Info: OPENAI_API_KEY not found. Skipping AI commentary.")
        return None
        
    try:
        from openai import OpenAI
        # The client will automatically use the OPENAI_API_KEY from environment variables
        client = OpenAI()

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful financial analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )
        
        # Extract response content
        return resp.choices[0].message.content

    except Exception as e:
        # Print specific error message instead of failing silently
        print(f" AI call failed. Reason: {e}")
        return None