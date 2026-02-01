# 📈 AI Agent: Technical Analyst (Enhanced Turtle)

**Module:** AI Agents in Asset Management (Track B)  
**Strategy Type:** Trend Following (Breakout) + Volatility Targeting  
**Account Type:** Margin Allowed (Max Leverage 1.5x)  
**Default Asset:** Amazon (AMZN)

---

## 1. Project Overview
This project implements an **AI Technical Analyst Agent** designed to simulate an institutional algorithmic trading desk. It prioritizes **Capital Preservation** during bear markets while capturing high-velocity trends using a modernized "Turtle Soup" logic.

Unlike predictive models, this agent employs a **Reactive Architecture**:
1.  **Regime Filter (The Shield):** A macro filter (SMA 200) that forces the agent into 100% Cash during systemic downtrends (e.g., 2022 Tech Crash).
2.  **Breakout Logic (The Engine):**
    - **Entry:** 20-Day Donchian High Breakout. Captures V-shaped recoveries faster than moving averages.
    - **Exit:** 10-Day Donchian Low Breakdown. A tight trailing stop to lock in profits.
3.  **Volatility Targeting (The Stabilizer):** Dynamically adjusts position sizing based on realized volatility (Target: 30% Ann. Vol).
    - Low Volatility -> Increase Leverage (Max 1.5x).
    - High Volatility -> Reduce Exposure.
4.  **AI-Powered Reporting:** Integrates **OpenAI (GPT-4o)** to generate professional Investment Memos with actionable advice.

---

## 2. File Structure
The codebase is organized for modularity, separating data ingestion, logic, and reporting.

```text
├── reports/                # OUTPUT FOLDER: Contains generated logs & charts
│   ├── trade_note.html     # The primary deliverable (Dashboard)
│   ├── trade_note.md       # Markdown version of the report
│   ├── trades.csv          # Transaction log
│   └── *.png               # Performance charts
├── src/
│   ├── __init__.py
│   ├── backtest.py         # Engine: PnL, Metrics, Financing Costs (4%)
│   ├── config.py           # Settings: Ticker, Dates, Strategy Params
│   ├── data.py             # Data Ingestion (yfinance)
│   ├── indicators.py       # Math: Volatility, SMA
│   ├── plotting.py         # Visualization: 4-Panel Dashboard
│   ├── report.py           # Reporting: HTML/MD generation
│   └── strategy.py         # Logic: Turtle Breakout + Vol Targeting
├── README.md               # Documentation
├── requirements.txt        # Dependencies
└── run_demo.py             # ENTRY POINT: Orchestrates the pipeline
```

---

## 3. Key Strategy Mechanics
The agent operates on a strict set of institutional rules designed for **Amazon (AMZN)**:

| Component | Logic | Purpose |
| :--- | :--- | :--- |
| **Trend Filter** | `Price > SMA(200)` | **The Shield.** Avoids "catching falling knives" during systemic Bear Markets (e.g., 2022). |
| **Entry Signal** | `Price > Max(High, 20)` | **The Engine.** Validates momentum strength before committing capital. Faster than moving averages. |
| **Exit Signal** | `Price < Min(Low, 10)` | **The Brake.** "Cut losers short." Functions as a tight dynamic trailing stop. |
| **Sizing** | `Target_Vol / Realized_Vol` | **The Stabilizer.** Risk Parity approach. Increases leverage in calm markets, decreases in chaos. |
| **Cost Model** | `Lev > 1` pays 4% interest | Realistic accounting for margin costs and idle cash yields. |

---

## 4. Installation
Ensure you have Python 3.10+ installed. 

1.  **Clone or Unzip** the project repository.
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

---

## 5. Usage
To fetch the latest data for the configured ticker (AMZN), run the backtest, and generate all reports:

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
A professional dashboard containing:
* **Current Investment Advice:** Clear "Maintain Long" or "Hold Cash" signals based on live data.
* **Key Metrics:** CAGR, Sharpe Ratio, Hit Rate compared against the Buy & Hold Benchmark.
* **AI Analyst Commentary:** Qualitative analysis of the strategy's performance drivers and risks.

**Performance Charts (Visual Evidence)**
1.  **Equity Curve:** Log-scale growth comparison (Strategy vs Benchmark).
2.  **Drawdown Profile:** Visualizes defensive performance (Red area) vs the Market (Grey area).
3.  **Volatility Control:** Shows how the agent adheres to the 30% risk target.
4.  **Leverage History:** Displays dynamic exposure (0.0x to 1.5x) over time.

**`trades.csv`**
A granular log of every rebalancing event for audit purposes.

---

## 7. Disclaimer
This software is for educational purposes only and is part of an MSc coursework submission. It does not constitute financial advice. The strategy involves the use of leverage which amplifies both gains and losses. Past performance is not indicative of future results.