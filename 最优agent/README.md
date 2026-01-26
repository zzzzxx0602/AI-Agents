# 📈 AI Agent: Technical Analyst (Volatility Targeting)

**Module:** AI Agents in Asset Management (Track B)
**Strategy Type:** Long-Only Trend Following with Dynamic Risk Control
**Default Asset:** Amazon (AMZN)

---

## 1. Project Overview
This project implements an **AI Technical Analyst Agent** designed to simulate a buy-side systematic trader. Unlike simple moving average crossovers, this agent employs a sophisticated **Volatility Targeting** mechanism to dynamically adjust leverage based on market risk regimes.

**Key Capabilities:**
* **Trend Identification:** Uses **Supertrend** for trend filtering and **Chandelier Exit** for trailing stops to "let winners run."
* **Institutional Risk Management:** Implements **Volatility Targeting**. The agent calculates realized rolling volatility and scales position sizes to maintain a constant risk profile (Target Vol: 10%).
* **AI-Powered Reporting:** Integrates **OpenAI (GPT-4o-mini)** to analyze backtest metrics and generate a structured, qualitative investment memo.
* **Dual-Format Output:** Generates both a raw Markdown report and a rich **HTML Dashboard** containing embedded base64 charts and strategy logic.

---

## 2. File Structure
The codebase is organized for modularity, separating data ingestion, logic, and reporting.

```text
├── data/                   # Folder for storing OHLCV data
├── reports/                # OUTPUT FOLDER: Contains generated logs, plots, and notes
│   ├── trade_note.html     # FINAL DELIVERABLE: Rich HTML dashboard with embedded charts
│   ├── trade_note.md       # Markdown version of the investment memo (for GitHub/docs)
│   ├── trades.csv          # Detailed log of every trade (Entry/Exit/PnL)
│   ├── equity_curve.csv    # Daily time-series data (Equity, Returns, Leverage, Volatility)
│   ├── equity_curve.png    # Visualization: Linear Equity Curve vs Benchmark
│   ├── equity_curve_log.png # Visualization: Log-Scale Equity Curve
│   └── rolling_vol.png     # Visualization: Strategy Realized Vol vs Target
├── src/
│   ├── config.py           # Central configuration (Params for Vol Target, ATR, etc.)
│   ├── data.py             # YFinance downloader and CSV loader
│   ├── indicators.py       # Numba/Pandas implementations of ATR, Supertrend, Chandelier
│   ├── strategy.py         # Signal generation logic (Entry/Exit rules)
│   ├── backtest.py         # Event-driven backtest engine
│   ├── plotting.py         # Matplotlib visualization logic
│   └── report.py           # LLM Prompting and HTML/Markdown builders
├── run_demo.py             # MAIN ENTRY POINT
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

---

## 3. Strategy Logic

### A. Signal Generation (`src/strategy.py`)
* **Entry:** Triggered when the price closes **above** the Supertrend Line (Bullish Regime).
* **Exit:** Triggered when:
    1.  Price closes **below** the **Chandelier Exit** (Trailing Stop).
    2.  OR Supertrend flips to Bearish.
    3.  OR a Hard Stop (based on ATR) is hit.

### B. Position Sizing: Volatility Targeting (`src/backtest.py`)
Instead of fixed lot sizes, the agent uses dynamic sizing to stabilize returns:
1.  **Calculate Volatility:** Computes the 60-day annualized rolling volatility (`strat_vol`) of the portfolio.
2.  **Determine Leverage:**
   $$ \text{Leverage} = \frac{\text{Target Volatility (10\%)}}{\text{Realized Volatility}} $$
3.  **Constraints:** Leverage is capped at **1.5x** (`max_leverage`) to prevent excessive risk during low-volatility regimes, and floored at 1.0x (`min_leverage`).

---

## 4. Installation & Setup

### Prerequisites
* Python 3.10+
* An OpenAI API Key (Existing key is configured in `run_demo.py`, but using an environment variable is recommended for security).

### Step 1: Install Dependencies
Navigate to the project root and install the required libraries:
```bash
pip install -r requirements.txt
```

### Step 2: Configuration
You can adjust the target asset and strategy parameters in `src/config.py`:
```python
@dataclass
class AgentConfig:
    ticker: str = "AMZN"        # Target Asset
    target_ann_vol: float = 0.10 # Target 10% Volatility
    max_leverage: float = 1.5   # Cap leverage
    ...
```

---

## 5. Usage

To run the agent, execute the demo script. This will download data, run the backtest, and generate the reports.

### Run with Live Data (YFinance)
```bash
python run_demo.py
```
*Downloads the last 10 years of AMZN data by default.*

### Run with Local CSV
If you have a custom dataset (must contain Open, High, Low, Close):
```bash
python run_demo.py --csv data/your_file.csv
```

---

## 6. Outputs & Interpretation

After the script finishes, the primary deliverable can be found in the `reports/` directory:

**`trade_note.html`**
Open this file in any web browser. It is a comprehensive dashboard containing:
* **Executive Summary:** Buy/Hold recommendation based on the latest signal.
* **Performance Metrics:** CAGR, Sharpe, Sortino vs Benchmark.
* **Charts:** Embedded interactive-style images of the Equity Curve and Rolling Volatility.
* **AI Commentary:** GPT-4o-mini's analysis of the backtest results.

---

## 7. Disclaimer
This software is for educational purposes only and is part of an MSc coursework submission. It does not constitute financial advice. The API Key included in the code is for demonstration purposes; do not use it for production environments.