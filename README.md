# 📈 AI Agent: Technical Analyst (Trend-Aware Volatility Targeting)

**Module:** AI Agents in Asset Management (Track B)  
**Strategy Type:** Volatility Targeting with Dynamic Risk Overlays  
**Account Type:** Margin Allowed (Max Leverage 1.5x)  
**Default Asset:** Amazon (AMZN)

---

## 1. Project Overview
This project implements an **AI Technical Analyst Agent** designed to simulate a quantitative researcher's workflow. It focuses on **Risk-Adjusted Returns** rather than pure directional betting.

Unlike simple buy-and-hold strategies, this agent incorporates **Dynamic Risk Management**:
1.  **Volatility Targeting:** Automatically scales position size inversely to market volatility (Target: 25% Ann. Vol).
2.  **Stepped Trend Filter:** Applies a **tiered risk control**.
    - **Defensive Mode (1.0x):** When Price < SMA but within a **10% buffer**. This tolerates normal market corrections without exiting.
    - **Crash Protection (Cash/0.0x):** Full exit only when the trend is deeply broken (>10% drop below SMA) to avoid catastrophic losses (e.g., 2022).
3.  **Momentum Filter:** Trims exposure during Overbought conditions (RSI > 80) to protect against reversals.
4.  **AI-Powered Reporting:** Integrates **OpenAI (GPT-4o)** to synthesize metrics and generate a professional Investment Memo.

---

## 2. File Structure
The codebase is organized for modularity, separating data ingestion, logic, and reporting.

```text
├── reports/                # OUTPUT FOLDER: Contains generated logs, plots, and notes
│   ├── trade_note.html     # >> FINAL DELIVERABLE: Rich HTML Strategy Report
│   ├── trade_note.md       # Markdown version of the investment memo
│   ├── backtest_chart.png  # Visualization: 4-Panel Dashboard (Equity, DD, Vol, Lev)
│   ├── trades_log.html     # Detailed table of holding periods (PnL colored)
│   ├── daily_transactions.html # Log of every daily rebalancing action
│   └── trades.csv          # Raw trade data for Excel analysis
├── src/                    # SOURCE CODE
│   ├── data.py             # Yahoo Finance Data Fetcher
│   ├── indicators.py       # Technical Indicator Library (Vol, SMA, RSI)
│   ├── strategy.py         # Core Logic: Vol Target + Risk Overlays
│   ├── backtest.py         # Backtest Engine & Metrics Calculation
│   ├── plotting.py         # Professional Matplotlib Charting
│   ├── report.py           # HTML/Markdown Report Generator & LLM Integration
│   └── config.py           # Global Parameters
├── run_demo.py             # MAIN ENTRY POINT: Orchestrates the workflow
├── requirements.txt        # Python Dependencies
└── README.md               # Documentation
```

---

## 3. Strategy Logic

### A. Core Engine: Volatility Targeting
The primary driver of position sizing is the volatility regime. The agent seeks to maintain a constant risk profile.
* **Target Volatility:** 25% (Annualized)
* **Lookback Window:** 20 Days

$$\text{Base Leverage} = \frac{\text{Target Volatility (0.25)}}{\text{Realized Volatility}_{20d}}$$

### B. Risk Overlays (The "Tri-Constraint" Logic)
The `src/strategy.py` applies dynamic caps to the Base Leverage based on market conditions:

1.  **Hard Cap Constraint:**
    Global safety limit to prevent excessive risk.
    $$\text{Max Leverage} = 1.5x$$

2.  **Trend Filter (Bearish Regime):**
    * **Logic:** If $\text{Price} < \text{SMA}_{200}$
    * **Action:** Market is fragile. Cap leverage at **1.0x** (De-leveraging).

3.  **Momentum Filter (Overbought):**
    * **Logic:** If $\text{RSI}_{14} > 80$
    * **Action:** Market is overextended. Cap leverage at **0.8x** (Trimming).

**Final Decision:**
$$\text{Executed Leverage} = \min( \text{Base Leverage}, \text{Dynamic Cap}, 1.5 )$$

---

## 4. Installation & Setup

### Prerequisites
* Python 3.10+
* An OpenAI API Key (Required for `src/report.py` to generate AI commentary).

### Step 1: Install Dependencies
Navigate to the project root and install the required libraries:
```bash
pip install -r requirements.txt
```

### Step 2: Configuration
You can adjust the core parameters in `src/config.py`:
```python
TICKER = "AMZN"        # Target Asset

# --- Core Strategy Parameters ---
VOL_WINDOW = 20        # Lookback window for realized volatility
TARGET_VOL = 0.25      # Target annualized volatility (25%)
MAX_LEVERAGE = 1.5     # Maximum allowed leverage ratio

# --- Risk Filters ---
SMA_WINDOW = 200       # Trend Filter Window
EXIT_BUFFER = 0.10     # Exit Threshold (10% below SMA triggers Cash Exit)
RSI_HIGH = 80          # Overbought Threshold

# --- Execution ---
COST_BPS = 10          # Transaction Cost (Basis Points)
RISK_FREE_RATE = 0.04  # Risk-Free Rate (4.0%)
REBALANCE_THRESHOLD = 0.10 # Buffer to reduce trading frequency
```

---

## 5. Usage

To run the agent, execute the demo script.

### Run Demo
This will fetch the latest data for the configured ticker (AMZN), run the backtest, and generate all reports:
```bash
python run_demo.py
```

> **Note on API Key:**
> The script requires an OpenAI API Key. Set it in your environment:
> `export OPENAI_API_KEY="sk-..."`
> Or configure it directly in `run_demo.py` for testing.

---

## 6. Outputs & Interpretation

After the script finishes, the primary deliverables can be found in the `reports/` directory:

**`trade_note.html`**
Open this file in any web browser. It is a comprehensive dashboard containing:
* **Executive Summary:** Current regime analysis (Bullish/Bearish) and Action Required.
* **Key Metrics:** CAGR, Sharpe Ratio, Sortino Ratio vs Benchmark.
* **AI Commentary:** GPT-4o's qualitative analysis of the strategy's efficiency.

**`backtest_chart.png`**
A 4-panel professional chart visualizing:
1.  **Equity Curve:** Strategy vs Benchmark (Log Scale).
2.  **Drawdown:** Historical depth of losses.
3.  **Volatility Regime:** Realized Vol vs Target Line.
4.  **Leverage Usage:** Visualizes the stepped de-leveraging process (1.5x -> 1.0x during corrections -> 0.0x during crashes).

**`trades_log.html`**
A detailed log showing every "Holding Period" (Entry to Exit), useful for auditing major trend captures.

---

## 7. Disclaimer
This software is for educational purposes only and is part of an MSc coursework submission. It does not constitute financial advice. The strategy involves the use of leverage which amplifies both gains and losses.