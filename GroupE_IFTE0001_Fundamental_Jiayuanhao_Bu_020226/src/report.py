import os
import json
import pandas as pd

def _df_to_html(df: pd.DataFrame, floatfmt: str = "{:,.4f}") -> str:
    """DataFrame to HTML """
    return df.to_html(
        border=0,
        classes="table",
        na_rep="--",
        float_format=lambda x: floatfmt.format(x) if pd.notna(x) and isinstance(x, (float, int)) else x
    )

def _dict_to_html_table(data_dict: dict, title: str) -> str:
    """Metric | Value"""
    if not data_dict:
        return f"<h3>{title}</h3><p>No data available.</p>"
    
    df = pd.DataFrame(list(data_dict.items()), columns=["Metric", "Value"])
    
    html = f"""
    <div class="card">
      <h3>{title}</h3>
      <table class="table">
        <thead><tr style="text-align: left;"><th>Metric</th><th>Value</th></tr></thead>
        <tbody>
    """
    for _, row in df.iterrows():
        val = row['Value']
        html += f"<tr><td><b>{row['Metric']}</b></td><td>{val}</td></tr>"
    html += "</tbody></table></div>"
    return html

def render_report_html(ticker: str, outputs, outputs_dir: str = "outputs", memo_path: str | None = None) -> str:
    os.makedirs(outputs_dir, exist_ok=True)

    try:
        ratios_df = pd.concat([
            outputs.gross_margin, 
            outputs.roe, 
            outputs.debt_to_equity, 
            outputs.asset_turnover
        ], axis=1)
        ratios_df.columns = ["Gross Margin", "ROE", "Debt-to-Equity", "Asset Turnover"]
    except Exception:
        ratios_df = pd.DataFrame()

    pe = outputs.pe_summary
    pe_clean = {}
    if pe:
        pe_clean = {
            "Current P/E (TTM)": f"{pe.get('pe_ttm', 0):.2f}",
            "Peer Median P/E": f"{pe.get('peer_median_pe', 0):.2f}",
            "Dynamic Red-line": f"{pe.get('dynamic_redline', 0):.2f}",
            "Screening Result": f"<span style='color:{'green' if pe.get('pe_result')=='Pass' else 'red'}; font-weight:bold'>{pe.get('pe_result')}</span>",
            "Assessment": f"<span style='font-size:0.9em; color:#555'>{pe.get('assessment')}</span>"
        }

    dcf = outputs.dcf_summary
    dcf_clean = {}
    if dcf:
        def fmt_money(x): return f"${x/1e9:,.1f} B" if x > 1e9 else f"${x:,.2f}"
        def fmt_pct(x): return f"{x*100:.2f}%"
        
        dcf_clean = {
            "TTM Revenue": fmt_money(dcf.get("ttm_revenue", 0)),
            "TTM Net Income": fmt_money(dcf.get("ttm_net_income", 0)),
            "Net Margin": fmt_pct(dcf.get("margin", 0)),
            "Assumed Growth Rate": fmt_pct(dcf.get("growth_rate", 0)),
            "Discount Rate (WACC)": fmt_pct(dcf.get("discount_rate", 0)),
            "Terminal Growth": fmt_pct(dcf.get("terminal_growth", 0)),
            "Calculated Equity Value": f"<b>${dcf.get('dcf_equity_value', 0)/1e12:,.2f} Trillion</b>"
        }

    memo_text = None
    if memo_path and os.path.exists(memo_path):
        with open(memo_path, "r", encoding="utf-8") as f:
            memo_text = f.read()

    memo_block = ""
    if memo_text:
        memo_block = f"""
  <div class="card" style="margin-top:16px;">
    <h2>Investment Memo (Markdown)</h2>
    <p class="muted">Source: <code>{os.path.basename(memo_path)}</code></p>
    <div style="background:#f9f9f9; padding:15px; border-radius:8px; line-height:1.6;">
        <pre style="background:transparent; border:none; padding:0; white-space: pre-wrap; font-family: inherit;">{memo_text}</pre>
    </div>
  </div>
"""

    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>AI Agent Report - {ticker}</title>
  <style>
    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 24px; background-color:
    h1,h2,h3 {{ margin-top: 0; color:
    h1 {{ font-size: 24px; margin-bottom: 5px; }}
    h2 {{ font-size: 18px; border-bottom: 2px solid
    h3 {{ font-size: 15px; color:
    
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }}
    .card {{ background: white; border: 1px solid
    
    .table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    .table th {{ background-color:
    .table td {{ padding: 10px; border-bottom: 1px solid
    .table tr:last-child td {{ border-bottom: none; }}
    
    .muted {{ color:
    code {{ background:
  </style>
</head>
<body>
  <h1>AI Financial Analysis Agent — Report</h1>
  <p class="muted">Ticker: <b>{ticker}</b> | Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}</p>

  <div class="grid">
    <div class="card">
      <h2>Income Statement (Summary)</h2>
      {_df_to_html(outputs.income_statement, "{:,.0f}")}
    </div>
    <div class="card">
      <h2>Balance Sheet (Summary)</h2>
      {_df_to_html(outputs.balance_sheet, "{:,.0f}")}
    </div>
  </div>

  <div class="card" style="margin-bottom: 20px;">
    <h2>Key Financial Ratios Trend</h2>
    <p style="font-size:13px; color:#666;">Consolidated view of Profitability, Returns, Leverage, and Efficiency.</p>
    {_df_to_html(ratios_df, "{:.2%}")} 
  </div>

  <div class="grid">
    {_dict_to_html_table(pe_clean, "Relative Valuation (P/E Dynamic Red-line)")}
    
    {_dict_to_html_table(dcf_clean, "Intrinsic Valuation (Minimal DCF)")}
  </div>

  <div class="card" style="margin-bottom: 20px;">
    <h2>Financial Risk (Altman Z-Score)</h2>
    {_df_to_html(outputs.altman_table)}
  </div>

  {memo_block}

  <p class="muted" style="text-align: center; margin-top: 40px;">Generated by AI Analyst Agent Framework</p>
</body>
</html>
"""
    out_path = os.path.join(outputs_dir, f"{ticker}_ai_agent_report.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return out_path



import base64
from datetime import date
from typing import Optional, List

_TRADE_NOTE_CSS = """body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; background-color: #f4f6f8; color: #333; }
.container { background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
.header { border-bottom: 2px solid
h1 { margin: 0; color:
h2 { color:
table { width: 100%; border-collapse: collapse; margin-top: 5px; font-size: 13px; }
th, td { padding: 8px; text-align: left; border-bottom: 1px solid
th { background-color:
.signal-box { padding: 6px 12px; background-color:
.recommendation { margin-top: 10px; padding: 10px; background-color:
.ai-commentary { background-color:
.footer { margin-top: 20px; border-top: 1px solid
"""

def _read_text(path: Optional[str]) -> Optional[str]:
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return None

def render_trade_note_html(
    ticker: str,
    outputs,
    outputs_dir: str = "reports",
    memo_path: str | None = None,
    chart_paths: Optional[List[str]] = None,
) -> str:
    os.makedirs(outputs_dir, exist_ok=True)
    pe = outputs.pe_summary or {}
    memo_text = _read_text(memo_path) or ""
    
    html = f"""<!DOCTYPE html><html><head><style>{_TRADE_NOTE_CSS}</style></head><body>
    <div class='container'>
        <div class='header'><h1>{ticker} Trade Note</h1></div>
        <div class='section'><h2>Investment Memo</h2><div class='ai-commentary'>{memo_text}</div></div>
    </div></body></html>"""
    
    out_path = os.path.join(outputs_dir, f"{ticker}_trade_note.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return out_path
