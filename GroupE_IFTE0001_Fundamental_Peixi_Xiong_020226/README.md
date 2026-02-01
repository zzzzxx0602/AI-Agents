# Fundamental Analyst AI Agent 

This repository implements a **Fundamental Analyst Agent** that:
- ingests 5+ years of financial statements,
- computes core ratios and drivers,
- runs a basic intrinsic valuation (WACC + FCF-DCF),
- and **uses an LLM to generate a 1–2 page investment memo** (key deliverable).

This is aligned with the coursework brief requirements for **Track A – Fundamental Analyst Agent** (data ingestion, ratio analysis, valuation, and an LLM-generated memo).  

Data source used in this demo: **Yahoo Finance via `yfinance`**.

---

## Quick Start

```bash
pip install -r requirements.txt
python run_demo.py
```

When prompted, enter a ticker, e.g.:
- US: `AAPL`, `MSFT`, `AMZN`
- UK: `ULVR.L`, `RR.L`, `BP.L`, `SHEL.L`

---

## LLM Setup (to generate the AI memo)

### Option 1 — OpenAI (default)
Set your API key in the environment:

- macOS/Linux:
```bash
export OPENAI_API_KEY="YOUR_KEY"
```

- Windows (PowerShell):
```powershell
setx OPENAI_API_KEY "YOUR_KEY"
```

Then run:
```bash
python run_demo.py
```

### Option 2 — Ollama (free/local)
1) Install Ollama and run it
2) In `src/config.py`, set:
- `llm_provider = "ollama"`
- `ollama_model = "llama3.1:8b"` (or any installed model)

Then run:
```bash
python run_demo.py
```

---

## Project Structure

```text
.
├── run_demo.py                          # End-to-end demo runner (generates all outputs in one run)
├── requirements.txt                     # Python dependencies
├── README.md                            # Documentation + run instructions
├── .env.example                         # Example environment file (OpenAI key)
├── src/
│   ├── __init__.py                      # Package init
│   ├── config.py                        # Global parameters (years, ERP, DCF, LLM provider)
│   ├── data.py                          # Data ingestion via yfinance + fiscal-year filter
│   ├── ratios.py                        # Ratios + DuPont drivers
│   ├── valuation.py                     # WACC + FCF-based DCF + sensitivity table
│   ├── plots.py                         # Price chart + DCF sensitivity heatmap
│   ├── io_utils.py                      # Excel exports (one table per workbook)
│   ├── prompts.py                       # LLM prompt builder (memo grounded in computed evidence)
│   ├── llm.py                           # LLM provider adapters (OpenAI or Ollama)
│   └── report.py                        # Save Markdown + HTML reports
├── data/                                # Auto-generated: extracted data + selected fields
├── tables/                              # Auto-generated: one Excel per table (no multi-sheet)
├── charts/                              # Auto-generated charts
└── reports/                             # Auto-generated reports (AI memo)
```

---

## What is computed?

### Ratios (from financial statements)
- **Profitability:** Gross / Operating / Net Margin (where available)
- **Efficiency:** Asset Turnover, ROE
- **Leverage & Liquidity:** Debt-to-Assets, Current Ratio
- **Growth:** Revenue YoY, Revenue CAGR (period)
- **Quality:** OCF / Net Income, FCF Margin

### Valuation
- **WACC:** CAPM (Rf + Beta×ERP), debt cost via interest/debt if available else fallback, tax rate inferred or fallback
- **DCF:** FCF = OCF − |CapEx|, 5-year projection, terminal value (Gordon growth), net-debt adjustment
- **Sensitivity:** WACC × terminal growth grid for fair value per share

---

## Outputs (generated after running `run_demo.py`)

### `reports/`
- `ai_investment_memo.md`  ✅ **LLM-generated 1–2 page investment memo**
- `ai_investment_memo.html` (print-friendly)

### `tables/` (each as a separate `.xlsx`)
- `ratios.xlsx`
- `drivers_dupont.xlsx`
- `wacc.xlsx`
- `dcf_summary.xlsx`
- `dcf_projection.xlsx`
- `dcf_sensitivity_table.xlsx`

### `data/`
- raw statements (`income_statement.xlsx`, `balance_sheet.xlsx`, `cashflow_statement.xlsx`)
- `market_info.xlsx`
- `selected_fields.xlsx` (auditable: which line-items were used)
- optional: `price_history_last_2y.xlsx`

### `charts/`
- `price_chart.png`
- `dcf_sensitivity_heatmap.png`

---

## Example: AI Memo (excerpt)

After you run the demo, open:
- `reports/ai_investment_memo.md`

This memo is produced by the LLM using the computed tables above and is explicitly instructed not to fabricate missing values.
