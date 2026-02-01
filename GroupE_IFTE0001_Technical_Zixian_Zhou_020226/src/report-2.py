import os
import base64
import pandas as pd
from datetime import datetime
from openai import OpenAI

class ReportGenerator:
    def __init__(self, client, output_dir="reports"):
        self.client = client
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def _image_to_base64(self, img_name):
        """Encodes image to Base64 for HTML embedding."""
        img_path = os.path.join(self.output_dir, img_name)
        if not os.path.exists(img_path):
            return ""
        with open(img_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')

    def _get_llm_analysis(self, ticker, metrics, bench_metrics, config, current_signal):
        """
        Generates analysis text via LLM with specific prompt engineering.
        """
        # Fallback text if no API Key provided
        if self.client is None:
            return (
                "- Slippage: Unexpected price changes during order execution can result in losses that deviate from expected outcomes.\n- Whipsaws: The strategy may experience false signals, leading to rapid entry and exit from positions, which can erode profitability.",
                f"Strategy Return: {metrics['Total Return']:.0%} vs Bench: {bench_metrics['Total Return']:.0%}. Alpha derived from filtering momentum (MACD) and trend (EMA).",
                f"Max Drawdown: {metrics['Max Drawdown']:.1%} vs Bench: {bench_metrics['Max Drawdown']:.1%}. Cash position during downtrends preserved capital.",
                f"Signal: {current_signal}. Execute based on strict rule adherence."
            )

        # Prompt Construction
        prompt = f"""
        You are a Senior Quantitative Analyst.
        Ticker: {ticker}
        Strategy: Dynamic Trend Following (EMA {config.EMA_SHORT}).
        
        Performance Data:
        - Strategy Return: {metrics['Total Return']:.2%}
        - Benchmark Return: {bench_metrics['Total Return']:.2%}
        - Strategy Drawdown: {metrics['Max Drawdown']:.2%}
        - Benchmark Drawdown: {bench_metrics['Max Drawdown']:.2%}
        - Sharpe Ratio: {metrics['Sharpe Ratio']:.2f}
        
        INSTRUCTIONS: 4 sections [PART X].
        
        [PART 1: STRUCTURAL_RISKS]
        Provide exactly 2 bullet points. Use concise, one-sentence descriptions.
        - Slippage: Unexpected price changes during order execution can result in losses that deviate from expected outcomes.
        - Whipsaws: The strategy may experience false signals, leading to rapid entry and exit from positions, which can erode profitability.
        
        [PART 2: EFFICIENCY]
        Analyze "Strategy Efficiency". 
        **CRITICAL: You MUST cite the specific Total Return ({metrics['Total Return']:.0%}) and Sharpe Ratio ({metrics['Sharpe Ratio']:.2f}) in your text to prove efficiency.**
        Start DIRECTLY with the data-driven insight. 
        Explain how MACD/RSI filters contributed to this performance.
        
        [PART 3: RISK_CONTROL]
        Analyze "Risk Management & Downside Analysis". 
        **CRITICAL: You MUST cite the specific Max Drawdown ({metrics['Max Drawdown']:.1%}) vs Benchmark ({bench_metrics['Max Drawdown']:.1%}) comparison.**
        Start DIRECTLY with the analysis of capital preservation.
        Explain how the Stop Loss mechanism achieved this result.
        
        [PART 4: ACTION]
        Actionable advice based on '{current_signal}'. Professional tone.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            content = response.choices[0].message.content
            parts = content.split("[PART")
            struct_risks = "- Analysis pending."
            efficiency = "Analysis pending."
            risk_control = "Analysis pending."
            action = "Hold."
            
            for p in parts:
                if "1: STRUCTURAL_RISKS]" in p: struct_risks = p.replace("1: STRUCTURAL_RISKS]", "").strip()
                elif "2: EFFICIENCY]" in p: efficiency = p.replace("2: EFFICIENCY]", "").strip()
                elif "3: RISK_CONTROL]" in p: risk_control = p.replace("3: RISK_CONTROL]", "").strip()
                elif "4: ACTION]" in p: action = p.replace("4: ACTION]", "").strip()
            
            return struct_risks, efficiency, risk_control, action
        except Exception as e:
            return "Error.", "Error.", "Error.", "Hold."

    def generate(self, ticker, metrics, bench_metrics, config, strategy_name, last_price, signal_status):
        print("Querying LLM for professional analysis...")
        struct_risks, eff_text, risk_ctrl_text, action_text = self._get_llm_analysis(ticker, metrics, bench_metrics, config, signal_status)
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        exec_action = "CONSIDER LONG ENTRY" if "Bullish" in signal_status else "MAINTAIN CASH / WAIT"
        
        def fmt(val, is_pct=True):
            if val is None: return "--"
            return f"{val:.2%}" if is_pct else f"{val:.2f}"

        table_rows = [
            ("Total Return", fmt(metrics['Total Return']), fmt(bench_metrics['Total Return']), "Net Profit"),
            ("CAGR", fmt(metrics['CAGR']), fmt(bench_metrics['CAGR']), "Annual Growth"),
            ("Sharpe Ratio", fmt(metrics['Sharpe Ratio'], False), fmt(bench_metrics['Sharpe Ratio'], False), "Risk-Adj Return"),
            ("Max Drawdown", fmt(metrics['Max Drawdown']), fmt(bench_metrics['Max Drawdown']), "Deepest Decline"),
            ("Hit Rate", fmt(metrics['Hit Rate']), "--", "Win Rate"),
            ("Total Trades", str(metrics['Total Trades']), "--", "Count")
        ]
        
        md_table = "\n".join([f"| **{r[0]}** | {r[1]} | {r[2]} | {r[3]} |" for r in table_rows])
        
        # [Markdown Report Structure]
        md_content = f"""# Trade Note — {ticker} ({date_str})
**Strategy:** {strategy_name}

## 1) Executive Summary
- **Signal:** {signal_status} (Price: {last_price:.2f})
- **Action:** {exec_action}

## 2) Key Metrics (vs Benchmark)
| Metric | Strategy | Benchmark | Description |
| :--- | :--- | :--- | :--- |
{md_table}

## 3) Strategy Configuration
- **Entry Signal:** Close > EMA {config.EMA_SHORT} + MACD Confirmed + RSI < 85
- **Exit Signal:** Close < EMA {config.EMA_SHORT} (Trend Reversal)
- **Stop Loss:** {config.STOP_LOSS_PCT:.1%} (Hard) / {config.TRAILING_STOP_PCT:.1%} (Trail)
- **Costs:** Comm {config.COMMISSION:.1%} + Slip {config.SLIPPAGE:.1%}

## 4) Structural Risks (Strategy Flaws)
{struct_risks}

## 5) AI Analyst Commentary
1. **Strategy Efficiency**:
   {eff_text}

2. **Risk Management & Downside Analysis**:
   {risk_ctrl_text}

3. **Actionable Investment Strategy**:
   {action_text}
"""
        
        # [HTML Report Structure]
        img_base64 = self._image_to_base64("performance_summary.png")
        img_html = ""
        if img_base64:
            img_html = f"""
            <h2>6) Visual Analysis</h2>
            <img src="data:image/png;base64,{img_base64}" alt="Chart">
            """
        
        html_rows = ""
        for r in table_rows:
            html_rows += f"<tr><td><b>{r[0]}</b></td><td><span class='highlight'>{r[1]}</span></td><td>{r[2]}</td><td>{r[3]}</td></tr>"

        risk_list_html = "".join([f"<li>{line.strip('- ')}</li>" for line in struct_risks.splitlines() if line.strip()])

        html_content = f"""
<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <title>Trade Note - {ticker}</title>
    <style>
        body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 30px; background-color: #f4f6f8; color: #333; line-height: 1.6; }}
        .container {{ background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
        .header {{ border-bottom: 2px solid #eaeaea; padding-bottom: 20px; margin-bottom: 20px; }}
        h1 {{ margin: 0; color: #2c3e50; font-size: 24px; }}
        .meta {{ color: #7f8c8d; font-size: 14px; margin-top: 5px; }}
        h2 {{ color: #2c3e50; border-left: 4px solid #3498db; padding-left: 10px; margin-top: 30px; font-size: 18px; }}
        .summary-box {{ background: #f8f9fa; padding: 15px; border-radius: 4px; border-left: 4px solid #2ecc71; }}
        .summary-item {{ margin-bottom: 5px; }}
        .label {{ font-weight: bold; color: #2c3e50; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 14px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #f0f0f0; }}
        th {{ background-color: #fafafa; font-weight: 600; color: #555; }}
        .highlight {{ color: #2980b9; font-weight: bold; }}
        .config-box {{ background: #fff; border: 1px solid #eee; padding: 15px; border-radius: 4px; font-size: 14px; }}
        img {{ width: 100%; border-radius: 4px; margin-top: 15px; border: 1px solid #eee; }}
        .ai-title {{ font-weight: bold; color: #2c3e50; font-size: 15px; display: block; margin-top: 15px; margin-bottom: 5px; }}
        .footer {{ margin-top: 40px; font-size: 12px; color: #999; text-align: center; border-top: 1px solid #eee; padding-top: 20px; }}
    </style>
</head>
<body>
    <div class='container'>
        <div class='header'>
            <h1>Trade Note: {ticker}</h1>
            <div class='meta'>{date_str} | {strategy_name}</div>
        </div>

        <h2>1) Executive Summary</h2>
        <div class='summary-box'>
            <div class='summary-item'><span class='label'>Signal:</span> {signal_status} (Price: {last_price:.2f})</div>
            <div class='summary-item'><span class='label'>Action:</span> {exec_action}</div>
        </div>

        <h2>2) Key Metrics (vs Benchmark)</h2>
        <table>
            <thead><tr><th>Metric</th><th>Strategy</th><th>Benchmark</th><th>Description</th></tr></thead>
            <tbody>{html_rows}</tbody>
        </table>

        <h2>3) Strategy Configuration</h2>
        <div class='config-box'>
            &bull; <b>Entry Signal:</b> Close > EMA {config.EMA_SHORT} + MACD Confirmed + RSI < 85<br>
            &bull; <b>Exit Signal:</b> Close < EMA {config.EMA_SHORT} (Trend Reversal)<br>
            &bull; <b>Stop Loss:</b> {config.STOP_LOSS_PCT:.1%} (Hard) / {config.TRAILING_STOP_PCT:.1%} (Trail)<br>
            &bull; <b>Costs:</b> Comm {config.COMMISSION:.1%} + Slip {config.SLIPPAGE:.1%}
        </div>

        <h2>4) Structural Risks (Strategy Flaws)</h2>
        <ul>{risk_list_html}</ul>

        <h2>5) AI Analyst Commentary</h2>
        <div class='ai-section'>
            <span class='ai-title'>1. Strategy Efficiency</span>
            <p>{eff_text}</p>
            
            <span class='ai-title'>2. Risk Management & Downside Analysis</span>
            <p>{risk_ctrl_text}</p>
            
            <span class='ai-title'>3. Actionable Investment Strategy</span>
            <p>{action_text}</p>
        </div>

        {img_html}

        <div class='footer'>Generated by AI Analyst Agent</div>
    </div>
</body>
</html>
"""
        with open(os.path.join(self.output_dir, "trade_note.md"), "w", encoding="utf-8") as f: f.write(md_content)
        with open(os.path.join(self.output_dir, "trade_note.html"), "w", encoding="utf-8") as f: f.write(html_content)
        return os.path.join(self.output_dir, "trade_note.md"), os.path.join(self.output_dir, "trade_note.html")