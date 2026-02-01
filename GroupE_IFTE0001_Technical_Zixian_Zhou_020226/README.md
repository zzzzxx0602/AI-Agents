# 📈 AI Agent: Technical Analyst (Dynamic Trend Following (EMA 40))

- **Module:** AI Agents in Asset Management (Track B)
- **Strategy Type:** Long-Only Trend Following with Volatility Targeting
- **Account Type:** Cash Account (No Margin / No Leverage)
- **Default Asset:** Amazon (AMZN)

---

## 1. Project Overview
This project fulfills the **Track B - Technical Analyst Agent** requirement for the "AI Agents in Asset Management" coursework. It simulates a professional quantitative workflow by building an autonomous agent that:
1.  **Ingests Market Data:** Fetches 10 years of OHLCV data using `yfinance`.
2.  **Applies Technical Logic:** Executes a trend-following strategy using EMA (40), MACD, and RSI filters.
3.  **Simulates Trading:** Runs a realistic backtest with transaction costs (commission & slippage) and volatility-based position sizing.
4.  **Generates Insight:** Uses an LLM (OpenAI GPT-4) to act as a Senior Quantitative Analyst, producing a professional trade note that evaluates efficiency and risk.

## 2. Strategy Logic
The agent implements a **Dynamic Trend Following** strategy designed to capture medium-term market moves while managing downside risk.

* **Entry Signal:**
    * Price > EMA 40 (Trend Confirmation)
    * MACD Bullish Crossover (Momentum Confirmation)
    * RSI < 85 (Overbought Protection)
* **Exit Signal:** Price crosses below EMA 40.
* **Risk Management:**
    * **Hard Stop:** 15% fixed stop loss.
    * **Trailing Stop:** 15% trailing stop to lock in profits.
    * **Position Sizing:** Volatility Targeting (scales exposure inversely to market volatility).

## 3. Project Structure

```text
.
├── run_demo.py             # Main execution script (End-to-End Demo)
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
├── src/                    # Source code modules
│   ├── config.py           # Global parameters (Ticker, Dates, Risk settings)
│   ├── data.py             # Data ingestion pipeline
│   ├── indicators.py       # Technical indicator calculations
│   ├── strategy.py         # Signal generation logic
│   ├── backtest.py         # Simulation engine & trade logging
│   ├── plotting.py         # Visualization (4-panel chart)
│   └── report.py           # LLM Prompt Engineering & Report Generation
└── reports/                # Output directory (Auto-generated artifacts)
    ├── performance_summary.png  # 4-Panel Dashboard: Equity, Volatility, Drawdown, Position
    ├── trades.csv               # Audit Log: Detailed record of all round-trip trades
    ├── trade_note.html          # Final Deliverable: Interactive HTML report with AI commentary
    └── trade_note.md            # Raw Text: Markdown source of the AI analysis
```

## 4. Installation & Setup

### Prerequisites
* Python 3.10+
* An OpenAI API Key

### Installation
Clone the repository, then run the following command to install dependencies:
```bash
pip install -r requirements.txt
```

### Configuration
1.  Open `src/config.py`.
2.  Set your target asset (e.g., `TICKER = "AMZN"`).
3.  Enter your OpenAI API Key:
    ```python
    OPENAI_API_KEY = "sk-..." 
    ```
    *(Note: If no key is provided, the agent will use placeholder text for the commentary, ensuring the code still runs without errors.)*

## 5. Running the Demo
To execute the full pipeline (Data -> Backtest -> Visualization -> Report), run:
```bash
python run_demo.py
```

## 6. Output Description
Upon successful execution, the `reports/` folder will populate with:

* **`performance_summary.png`**: A comprehensive visual analysis containing four subplots:
    1.  *Equity Curve*: Strategy vs Benchmark (Buy & Hold).
    2.  *Rolling Volatility*: Risk comparison over time.
    3.  *Drawdown*: Depth and duration of losses.
    4.  *Position Size*: Historical market exposure (Shares held).
* **`trades.csv`**: A CSV file listing every executed trade, including Entry Date, Exit Date, Entry/Exit Price, PnL, and the specific reason for exit (e.g., Signal, Stop Loss).
* **`trade_note.html`**: A polished, browser-viewable report simulating a sell-side research note. It combines the visual charts with the AI Agent's structural risk analysis and efficiency evaluation.

## 7. Disclaimer
This software is for educational purposes only as part of the MSc coursework. It is not financial advice.