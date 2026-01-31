# src/report.py
from __future__ import annotations

import os
import base64
import re
import pandas as pd


# ---------- formatting ----------
def format_pct(x: float) -> str:
    if x is None or pd.isna(x):
        return "n/a"
    return f"{x*100:.2f}%"

def format_num(x: float) -> str:
    if x is None or pd.isna(x):
        return "n/a"
    return f"{x:,.3f}"

def image_to_base64(img_path: str) -> str:
    if (not img_path) or (not os.path.exists(img_path)):
        return ""
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def markdown_to_html(text: str) -> str:
    """
    Lightweight markdown -> HTML for AI commentary block
    - **bold** -> <b>bold</b>
    - "- " bullets -> bullets
    - newlines -> <br>
    """
    if not text:
        return ""
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    text = text.replace("\n- ", "<br>&bull; ")
    text = text.replace("- ", "&bull; ")
    text = text.replace("\n", "<br>")
    return text


# ---------- signal/action logic ----------
def vol_overlay_signal_and_action(latest_state: dict, params: dict) -> tuple[str, str]:
    rv = latest_state.get("realized_vol_annualized", None)
    tv = params.get("target_vol", None)
    exp_exec = latest_state.get("executed_exposure", None)
    exp_sug = latest_state.get("suggested_exposure", None)

    if rv is None or tv is None or pd.isna(rv) or pd.isna(tv):
        return "Signal: n/a", "ACTION: Hold / insufficient data."

    if rv > tv * 1.20:
        signal = f"High Vol Regime (AnnVol={rv:.2%} > Target={tv:.2%})"
        action = "ACTION: Reduce risk / maintain defensive posture (lower exposure)."
    elif rv < tv * 0.80:
        signal = f"Low Vol Regime (AnnVol={rv:.2%} < Target={tv:.2%})"
        action = "ACTION: Risk budget available (can increase/maintain exposure)."
    else:
        signal = f"Balanced Vol Regime (AnnVol={rv:.2%} ~ Target={tv:.2%})"
        action = "ACTION: Maintain exposure; rebalance only if threshold triggers."

    if exp_exec is not None and exp_sug is not None and (not pd.isna(exp_exec)) and (not pd.isna(exp_sug)):
        signal += f" | ExecExp={exp_exec:.2f}, SugExp={exp_sug:.2f}"

    return signal, action


# ---------- LLM prompt + call ----------
def build_vol_overlay_llm_prompt(ticker: str, as_of: str, params: dict, metrics: dict, latest_state: dict) -> str:
    prompt = f"""
You are a buy-side risk overlay analyst. Write a concise "AI Market Analysis" for a Volatility Targeting Overlay (Vol Overlay) on {ticker}.
Follow EXACT style rules:
- Output MUST be 3 numbered sections (1., 2., 3.)
- Each section starts with a **bold heading** (use **Heading**)
- Use short bullet points with "- " and line breaks
- Mention the key numbers given
- Keep it practical: regime, risk, and actionable next steps
- Stay under 170 words

Context (as of {as_of}):
- Target annual vol: {params.get("target_vol")}
- Realized annual vol (latest): {latest_state.get("realized_vol_annualized")}
- Suggested exposure (latest): {latest_state.get("suggested_exposure")}
- Executed exposure (latest): {latest_state.get("executed_exposure")}
- Rebalance threshold: {params.get("rebalance_threshold")}

Backtest metrics (strategy vs buy&hold benchmark):
- Strategy Total Return: {metrics.get("TotalReturn_strategy")}
- Buy&Hold Total Return: {metrics.get("TotalReturn_buy_hold")}
- Strategy CAGR: {metrics.get("CAGR_strategy")}
- Buy&Hold CAGR: {metrics.get("CAGR_buy_hold")}
- Strategy Sharpe: {metrics.get("Sharpe_strategy")}
- Max Drawdown (strategy): {metrics.get("MaxDD_strategy")}
- Hit Rate (strategy): {metrics.get("HitRate_strategy")}
- Rebalance trades: {metrics.get("Rebalance_trades")}

Now write the analysis.
""".strip()
    return prompt

def try_generate_llm_commentary(prompt: str) -> str | None:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("Info: OPENAI_API_KEY not found. Skipping AI commentary.")
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful financial analyst."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content

    except Exception as e:
        print(f"AI call failed. Reason: {e}")
        return None


# ---------- Markdown report ----------
def build_trade_note_markdown_vol_overlay(
    ticker, params, metrics, signal_text, action_text, as_of, llm_text=None
) -> str:
    lines = []
    lines.append(f"# Trade Note — {ticker} ({as_of})")
    lines.append("**Strategy:** Volatility Targeting Overlay (Defensive Vol Control)")
    lines.append("")
    lines.append("## 1) Executive Summary")
    lines.append(f"- **Signal:** {signal_text}")
    lines.append(f"- **Action:** {action_text.replace('ACTION: ', '')}")
    lines.append("")
    lines.append("## 2) Key Metrics")
    lines.append("| Metric | Strategy | Buy & Hold |")
    lines.append("| :--- | :--- | :--- |")
    lines.append(f"| **Total Return** | {format_pct(metrics.get('TotalReturn_strategy'))} | {format_pct(metrics.get('TotalReturn_buy_hold'))} |")
    lines.append(f"| **CAGR** | {format_pct(metrics.get('CAGR_strategy'))} | {format_pct(metrics.get('CAGR_buy_hold'))} |")
    lines.append(f"| **Sharpe** | {format_num(metrics.get('Sharpe_strategy'))} | {format_num(metrics.get('Sharpe_buy_hold'))} |")
    lines.append(f"| **Max DD** | {format_pct(metrics.get('MaxDD_strategy'))} | {format_pct(metrics.get('MaxDD_buy_hold'))} |")
    lines.append(f"| **Hit Rate** | {format_pct(metrics.get('HitRate_strategy'))} | -- |")
    lines.append("")
    lines.append("## 3) Strategy Configuration")
    lines.append(f"- **Window (days):** {params.get('window_days')}")
    lines.append(f"- **Target Vol:** {params.get('target_vol')}")
    lines.append(f"- **Exposure Range:** [{params.get('min_exposure')}, {params.get('max_exposure')}]")
    lines.append(f"- **Rebalance Threshold:** {params.get('rebalance_threshold')}")
    lines.append(f"- **Rebalance Trades:** {metrics.get('Rebalance_trades')}")
    if llm_text:
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 4) AI Market Analysis")
        lines.append(llm_text.strip())
    return "\n".join(lines)


# ---------- HTML report ----------
def build_trade_note_html_vol_overlay(
    ticker, params, metrics, signal_text, action_text, as_of, charts: dict, llm_text=None
) -> str:
    # regime color
    is_high_vol = "High Vol" in (signal_text or "")
    status_color = "#d9534f" if is_high_vol else "#5cb85c"
    advice_color = "#fdebd0" if is_high_vol else "#d4efdf"
    advice_text_color = "#d35400" if is_high_vol else "#186a3b"

    # base64 images
    img_equity = image_to_base64(charts.get("equity", ""))
    img_vol = image_to_base64(charts.get("vol", ""))
    img_exposure = image_to_base64(charts.get("exposure", ""))
    img_drawdown = image_to_base64(charts.get("drawdown", ""))

    html = []
    html.append("<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'><style>")
    html.append("body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; max-width: 980px; margin: 0 auto; padding: 20px; background-color: #f4f6f8; color: #333; }")
    html.append(".container { background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }")
    html.append(".header { border-bottom: 2px solid #eaeaea; padding-bottom: 10px; margin-bottom: 15px; display: flex; justify-content: space-between; gap: 12px; }")
    html.append("h1 { margin: 0; color: #2c3e50; font-size: 22px; }")
    html.append("h2 { color: #2c3e50; border-left: 4px solid #3498db; padding-left: 10px; margin-top: 20px; margin-bottom: 10px; font-size: 16px; }")
    html.append("table { width: 100%; border-collapse: collapse; margin-top: 5px; font-size: 13px; }")
    html.append("th, td { padding: 8px; text-align: left; border-bottom: 1px solid #f0f0f0; }")
    html.append("th { background-color: #fafafa; font-weight: 600; }")
    html.append(f".signal-box {{ padding: 6px 12px; background-color: {status_color}; color: white; border-radius: 4px; font-weight: bold; display: inline-block; font-size: 13px; }}")
    html.append(f".recommendation {{ margin-top: 10px; padding: 10px; background-color: {advice_color}; border-radius: 4px; color: {advice_text_color}; font-weight: bold; border: 1px solid {status_color}; font-size: 13px; }}")
    html.append(".ai-commentary { background-color: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #9b59b6; line-height: 1.5; color: #444; font-size: 13px; }")
    html.append(".chart-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 10px; }")
    html.append(".chart-item { background:#fff; border:1px solid #eee; border-radius:6px; padding:10px; }")
    html.append(".chart-item .cap { font-size:12px; color:#555; margin-bottom:6px; font-weight:600; }")
    html.append(".chart-item img { width: 100%; border-radius: 4px; }")
    html.append(".footer { margin-top: 20px; border-top: 1px solid #ddd; padding-top: 10px; font-size: 10px; color: #999; text-align: center; }")
    html.append(".config-list { font-size: 13px; padding-left: 20px; margin: 0; }")
    html.append(".config-list li { margin-bottom: 4px; }")
    html.append("</style><title>Trade Note</title></head><body>")

    html.append("<div class='container'><div class='header'>")
    html.append(f"<div><h1>{ticker} Vol Overlay Report</h1><div style='color:#7f8c8d; font-size:12px; margin-top:2px;'>Date: {as_of} | AI Generated</div></div>")
    html.append(f"<div style='text-align:right; font-size:11px; color:#666;'><strong>Model:</strong> Volatility Targeting Overlay<br><strong>Asset:</strong> {ticker}</div>")
    html.append("</div>")

    # 1) Signal & Action
    html.append("<div class='section'><h2>1. Signal & Action</h2>")
    html.append(f"<div class='signal-box'>{signal_text}</div>")
    html.append(f"<div class='recommendation'>{action_text}</div></div>")

    # 2) Key Metrics
    html.append("<div class='section'><h2>2. Key Metrics</h2>")
    html.append("<table><thead><tr><th>Metric</th><th>Strategy</th><th>Benchmark</th><th>Notes</th></tr></thead><tbody>")
    html.append(f"<tr><td>Total Return</td><td>{format_pct(metrics.get('TotalReturn_strategy'))}</td><td>{format_pct(metrics.get('TotalReturn_buy_hold'))}</td><td>Cumulative</td></tr>")
    html.append(f"<tr><td>CAGR</td><td>{format_pct(metrics.get('CAGR_strategy'))}</td><td>{format_pct(metrics.get('CAGR_buy_hold'))}</td><td>Annualized</td></tr>")
    html.append(f"<tr><td>Sharpe Ratio</td><td>{format_num(metrics.get('Sharpe_strategy'))}</td><td>{format_num(metrics.get('Sharpe_buy_hold'))}</td><td>Risk-adjusted</td></tr>")
    html.append(f"<tr><td>Max Drawdown</td><td>{format_pct(metrics.get('MaxDD_strategy'))}</td><td>{format_pct(metrics.get('MaxDD_buy_hold'))}</td><td>Worst peak-to-trough</td></tr>")
    html.append(f"<tr><td>Hit Rate</td><td>{format_pct(metrics.get('HitRate_strategy'))}</td><td>--</td><td>Next-day win after rebalance</td></tr>")
    html.append("</tbody></table></div>")

    # 3) Performance Visualization (4 key charts)
    html.append("<div class='section'><h2>3. Performance Visualization</h2>")
    html.append("<div class='chart-grid'>")

    if img_equity:
        html.append("<div class='chart-item'><div class='cap'>Equity Curve</div>")
        html.append(f"<img src='data:image/png;base64,{img_equity}' alt='Equity Curve'></div>")

    if img_vol:
        html.append("<div class='chart-item'><div class='cap'>Rolling Realized Vol</div>")
        html.append(f"<img src='data:image/png;base64,{img_vol}' alt='Rolling Vol'></div>")

    if img_exposure:
        html.append("<div class='chart-item'><div class='cap'>Exposure (Position Size)</div>")
        html.append(f"<img src='data:image/png;base64,{img_exposure}' alt='Exposure'></div>")

    if img_drawdown:
        html.append("<div class='chart-item'><div class='cap'>Drawdown Comparison</div>")
        html.append(f"<img src='data:image/png;base64,{img_drawdown}' alt='Drawdown Comparison'></div>")

    html.append("</div></div>")

    # 4) Strategy Configuration
    html.append("<div class='section'><h2>4. Strategy Configuration</h2>")
    html.append("<ul class='config-list'>")
    html.append(f"<li><strong>Window:</strong> {params.get('window_days')} trading days</li>")
    html.append(f"<li><strong>Target Vol:</strong> {params.get('target_vol')}</li>")
    html.append(f"<li><strong>Exposure Range:</strong> {params.get('min_exposure')} to {params.get('max_exposure')}</li>")
    html.append(f"<li><strong>Rebalance Threshold:</strong> {params.get('rebalance_threshold')} <span style='color:#ccc'>|</span> Trades: {metrics.get('Rebalance_trades')}</li>")
    html.append("</ul></div>")

    # 5) AI Market Analysis
    if llm_text:
        html.append("<div class='section'><h2>5. AI Market Analysis</h2>")
        html.append(f"<div class='ai-commentary'>{markdown_to_html(llm_text)}</div></div>")

    html.append("<div class='footer'>Disclaimer: Educational purpose only. Not financial advice.</div>")
    html.append("</div></body></html>")
    return "".join(html)
