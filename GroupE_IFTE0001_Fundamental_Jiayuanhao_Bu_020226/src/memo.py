import os
from datetime import date
from typing import Optional, Tuple
import pandas as pd
import yfinance as yf

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


def _trend(series: pd.Series, higher_is_better: bool = True) -> str:
    """Return 'improving', 'deteriorating', or 'stable' based on first vs last non-null values."""
    s = series.dropna()
    if len(s) < 2:
        return "stable"
    first = float(s.iloc[0])
    last = float(s.iloc[-1])
    if higher_is_better:
        if last > first:
            return "improving"
        if last < first:
            return "deteriorating"
        return "stable"
    else:
        if last < first:
            return "improving"
        if last > first:
            return "deteriorating"
        return "stable"

def _fmt_money(value: Optional[float]) -> str:
    if value is None:
        return "N/A"
    return f"${value:,.2f}"

def _fmt_pct(x: Optional[float], digits: int = 1) -> str:
    if x is None:
        return "N/A"
    return f"{x * 100:.{digits}f}%"

def _get_company_name(ticker: str, info: dict) -> str:
    return info.get("longName") or info.get("shortName") or ticker.upper()

def compute_market_sanity_check(
    ticker: str,
    dcf_equity_value: float
) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float], str]:
    """
    DCF
    LLM 
    """
    stock = yf.Ticker(ticker)
    info = stock.info or {}

    market_cap = info.get("marketCap", None)
    shares_outstanding = info.get("sharesOutstanding", None)
    current_price = info.get("currentPrice", None) or info.get("regularMarketPrice", None)

    fair_value_per_share = None
    if shares_outstanding and shares_outstanding > 0:
        fair_value_per_share = dcf_equity_value / shares_outstanding

    upside_pct = None
    if market_cap and market_cap > 0:
        upside_pct = (dcf_equity_value / market_cap) - 1

    price_upside_pct = None
    if fair_value_per_share is not None and current_price and current_price > 0:
        price_upside_pct = (fair_value_per_share / current_price) - 1

    effective_upside = price_upside_pct if price_upside_pct is not None else upside_pct

    model_uncertainty_band = 0.10
    buy_threshold = 0.25 + model_uncertainty_band
    sell_threshold = -0.20 - model_uncertainty_band

    recommendation = "HOLD"
    if effective_upside is not None:
        if effective_upside > buy_threshold:
            recommendation = "BUY"
        elif effective_upside < sell_threshold:
            recommendation = "SELL"

    return market_cap, current_price, fair_value_per_share, price_upside_pct, recommendation


def generate_investment_memo(ticker: str, outputs, as_of: Optional[str] = None) -> str:
    """
    LLM (OpenAI API) 。
    Prompt to LLM。
    """
    
    api_key = os.getenv("OPENAI API KEY")
    if not OpenAI:
        return "**Error:** `openai` library not installed. Please run `pip install openai`."
    if not api_key:
        return "**Error:** `OPENAI_API_KEY` environment variable not found. Please set your API key."

    client = OpenAI(api_key=api_key)
    
    if as_of is None:
        as_of = date.today().isoformat()
    
    ticker = ticker.upper()
    stock = yf.Ticker(ticker)
    info = stock.info or {}
    company_name = _get_company_name(ticker, info)


    def get_last(df): return float(df.dropna().iloc[-1, 0]) if not df.empty else None
    
    gm_val = get_last(outputs.gross_margin)
    gm_trend = _trend(outputs.gross_margin["Gross Margin"], higher_is_better=True)
    
    roe_val = get_last(outputs.roe)
    roe_trend = _trend(outputs.roe["ROE"], higher_is_better=True)
    
    de_val = get_last(outputs.debt_to_equity)
    de_trend = _trend(outputs.debt_to_equity["Debt-to-Equity"], higher_is_better=False)
    
    at_val = get_last(outputs.asset_turnover)
    at_trend = _trend(outputs.asset_turnover["Asset Turnover"], higher_is_better=True)

    alt = outputs.altman_table.dropna()
    z_score = float(alt.iloc[-1]["Altman_Z_Score"]) if not alt.empty else "N/A"
    z_zone = str(alt.iloc[-1]["Financial_Risk_Zone"]) if not alt.empty else "Unknown"

    pe_data = outputs.pe_summary
    pe_ttm = pe_data.get("pe_ttm")
    peer_median = pe_data.get("peer_median_pe")
    dynamic_redline = pe_data.get("dynamic_redline")
    pe_assessment = pe_data.get("assessment", "N/A")

    dcf = outputs.dcf_summary
    dcf_val = dcf.get("dcf_equity_value", 0.0)
    
    market_cap, current_price, fair_value, upside, rec_model = compute_market_sanity_check(ticker, dcf_val)

    system_prompt = (
        "You are a professional Buy-Side Equity Research Analyst at a top-tier asset management firm. "
        "Your job is to write a concise, data-driven Investment Memorandum based strictly on the provided financial data. "
        "Do not hallucinate financial figures. Use the provided metrics to support your arguments. "
        "Your tone should be professional, objective, and critical."
    )

    data_context = f"""
    TARGET COMPANY: {company_name} ({ticker})
    DATE: {as_of}

    === QUANTITATIVE MODEL OUTPUTS ===
    1. PROFITABILITY & EFFICIENCY:
       - Gross Margin: {_fmt_pct(gm_val)} (Trend: {gm_trend})
       - ROE: {_fmt_pct(roe_val)} (Trend: {roe_trend})
       - Asset Turnover: {at_val:.2f} (Trend: {at_trend})
    
    2. LEVERAGE & RISK:
       - Debt-to-Equity: {de_val:.2f} (Trend: {de_trend})
       - Altman Z-Score: {z_score} (Risk Zone: {z_zone})
    
    3. RELATIVE VALUATION (P/E):
       - Current P/E (TTM): {pe_ttm}
       - Peer Median P/E: {peer_median}
       - Dynamic Red-line Threshold: {dynamic_redline}
       - Model Flag: {pe_assessment}
    
    4. INTRINSIC VALUATION (DCF):
       - DCF Equity Value: ${_fmt_money(dcf_val)}
       - Fair Value per Share: ${_fmt_money(fair_value)}
       - Current Market Price: ${_fmt_money(current_price)}
       - Implied Upside/Downside: {_fmt_pct(upside)}
       - Model Inputs: Growth Rate={_fmt_pct(dcf.get('growth_rate'))}, WACC/Discount={_fmt_pct(dcf.get('discount_rate'))}

    5. AUTOMATED MODEL RECOMMENDATION: {rec_model}
    """

    user_instructions = """
    Please write a 1-2 page Investment Memo in Markdown format using the structure below. 
    Critically analyze the data provided above. If the data is mixed (e.g., strong valuation but poor momentum), explain the conflict.

    **Structure:**
    **1. Executive Summary:** Briefly state the investment thesis and the final recommendation (BUY/HOLD/SELL).
    **2. Business Overview:** Briefly describe what the company does (use your internal knowledge for this part only).
    **3. Financial Health Analysis:** Discuss the ratios (Margin, ROE, Debt) and the Altman Z-score. Are they improving or deteriorating?
    **4. Valuation Assessment:** Compare the Intrinsic Value (DCF) vs. Market Price, and the P/E relative to peers.
    **5. Investment Risks:** Based on the data (e.g., high debt, falling margins) and general sector risks.
    **6. Final Verdict:** A conclusive paragraph summarizing why you chose the recommendation.

    Note: Ensure the output is clean Markdown suitable for direct rendering.
    """

    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": data_context + "\n" + user_instructions}
            ],
            temperature=0.7
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"**Error generating memo with LLM:** {str(e)}\n\n(Fallback to raw data display)\n{data_context}"

def save_memo(memo_text: str, outputs_dir: str, ticker: str) -> str:
    os.makedirs(outputs_dir, exist_ok=True)
    path = os.path.join(outputs_dir, f"{ticker.upper()}_investment_memo.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(memo_text)
    return path
