# Volatility Targeting Overlay Agent (AMZN)

This project implements a volatility targeting overlay (defensive risk control) and generates a teammate-style trade note report.

## Project Structure
- `src/`: core modules (data, strategy, metrics, report)
- `run_demo.py`: one-click runnable demo script
- `reports/`: generated charts and reports (created after running)

## Core components
- Drawdown-based defensive overlay: linearly reduces exposure as peak-to-trough drawdowns deepen, providing capital protection during prolonged downturns.
- Tail-risk crash brake: detects extreme negative return events using fast volatility estimates and temporarily caps exposure during crash regimes.
- Downside volatility control: applies additional exposure reduction when downside volatility rises, activated only during sufficiently negative drawdown states.

The three overlays are multiplicatively combined and smoothed using asymmetric adjustment speeds to control turnover.  
Portfolio exposure is implemented with a one-day lag to prevent look-ahead bias.

## Backtesting features
- Daily rebalanced exposure based on historical price data.
- Transaction costs modelled as 0.1% per unit of portfolio turnover.
- Performance evaluation using CAGR, maximum drawdown, hit rate, and risk-adjusted Sharpe ratio (excess return over a 4% annual risk-free rate).

Outputs include equity curves, drawdown comparison, exposure dynamics, and an LLM-generated analytical trade note.
## How to Run
1) Install dependencies
```bash
pip install -r requirements.txt
