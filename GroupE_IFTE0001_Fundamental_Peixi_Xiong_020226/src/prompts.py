from __future__ import annotations
import json
import pandas as pd

def _df_tail_as_markdown(df: pd.DataFrame, n: int = 6) -> str:
    if df is None or df.empty:
        return "_No data available._"
    tail = df.tail(n).copy()
    # shorten columns if huge
    if tail.shape[1] > 12:
        tail = tail.iloc[:, :12]
    return tail.to_markdown()

def build_investment_memo_prompt(
    symbol: str,
    company_name: str | None,
    market_info: dict,
    ratios_df: pd.DataFrame,
    drivers_df: pd.DataFrame,
    wacc_res: dict,
    dcf_res: dict,
    sensitivity_df: pd.DataFrame,
) -> dict:
    # We feed compact, auditable numeric context, and ask for a structured memo.
    # The coursework requires LLM-generated memo grounded in finance logic and citing data sources.
    context = {
        "symbol": symbol,
        "company_name": company_name,
        "market_snapshot": {
            "price": market_info.get("currentPrice"),
            "market_cap": market_info.get("marketCap"),
            "shares_outstanding": market_info.get("sharesOutstanding"),
            "beta": market_info.get("beta"),
        },
        "wacc": wacc_res,
        "dcf_summary": dcf_res,
    }

    system = (
        "You are a buy-side equity research analyst at an asset management firm. "
        "Write a concise 1–2 page investment memo in professional English. "
        "Your memo must be grounded in the provided numeric evidence and standard finance logic. "
        "Do NOT fabricate financial figures; if a datapoint is missing, say it is unavailable. "
        "Explicitly cite the data source as: 'Yahoo Finance via yfinance' and reference the years covered."
    )

    user = f"""Write an **investment memo** for {symbol} ({company_name or 'company'}). 

## Requirements
- Length: ~1–2 pages (roughly 700–1200 words)
- Structure with headings:
  1) Investment Thesis (Bull/Base/Bear)
  2) Fundamental Snapshot (profitability, efficiency, leverage/liquidity, growth, quality)
  3) Valuation (WACC + DCF) and implied upside/downside
  4) Key Risks & Risk Mitigations
  5) Catalyst Watchlist (3–5)
  6) Recommendation: **Buy / Hold / Sell**, include a clear rationale and a confidence level (Low/Med/High)
- MUST cite data source: Yahoo Finance via yfinance.
- Use the tables below as evidence. When possible, quote the latest-year ratios and discuss trends.

## Compact JSON context (do not repeat verbatim; use it to reason)
```json
{json.dumps(context, indent=2)}
```

## Ratio table (tail)
{_df_tail_as_markdown(ratios_df)}

## Drivers / DuPont table (tail)
{_df_tail_as_markdown(drivers_df)}

## DCF sensitivity (fair value per share) – grid
{_df_tail_as_markdown(sensitivity_df)}

Return the memo in Markdown.
"""
    return {"system": system, "user": user}
