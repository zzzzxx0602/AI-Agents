"""run_demo.py — End-to-end Fundamental Analyst AI Agent (PyCharm friendly)

What this script does (single run):
1) Pulls 5+ years of company statements (target 2019–2024) from Yahoo Finance via yfinance
2) Computes financial ratios (profitability, leverage, growth, efficiency, quality)
3) Computes WACC + a simple but standard FCF-based DCF valuation
4) Generates DCF sensitivity table + charts
5) Calls an LLM to write a 1–2 page **AI investment memo** (key coursework deliverable)
6) Exports:
   - data/    extracted statements + market snapshot + selected_fields
   - tables/  one Excel per table (no multi-sheet workbooks)
   - charts/  PNGs (price + DCF sensitivity heatmap)
   - reports/ Markdown + HTML AI memo

Run:
    pip install -r requirements.txt
    python run_demo.py

LLM options:
- OpenAI (default): set environment variable OPENAI_API_KEY
- Ollama (free/local): install Ollama + run it, then set Config.llm_provider="ollama" in src/config.py
"""

from pathlib import Path
import pandas as pd

from src.config import Config
from src.data import fetch_market_info, fetch_risk_free_rate, fetch_statements, filter_fiscal_years, fetch_price_history
from src.ratios import compute_core_ratios, compute_drivers
from src.valuation import compute_wacc, compute_dcf, sensitivity_table
from src.io_utils import write_excel, write_kv_excel
from src.plots import plot_price, plot_sensitivity_heatmap
from src.prompts import build_investment_memo_prompt
from src.llm import generate_ai_memo
from src.report import save_md_html

def main():
    cfg = Config()
    symbol = input("Enter Equity Ticker (e.g., AAPL / MSFT / ULVR.L): ").strip().upper()
    if not symbol:
        raise SystemExit("Ticker is required.")

    root = Path(__file__).resolve().parent

    # --- 1) Pull market + statements
    ticker, info = fetch_market_info(symbol)
    rf = fetch_risk_free_rate(cfg.risk_free_proxy)

    income_df, balance_df, cashflow_df = fetch_statements(ticker)
    income_df = filter_fiscal_years(income_df, cfg.fiscal_years)
    balance_df = filter_fiscal_years(balance_df, cfg.fiscal_years)
    cashflow_df = filter_fiscal_years(cashflow_df, cfg.fiscal_years)

    # price context (optional)
    price_df = fetch_price_history(symbol, years=5)

    # --- 2) Ratios + Drivers
    ratios_df, selected_fields = compute_core_ratios(income_df, balance_df, cashflow_df)
    drivers_df = compute_drivers(income_df, balance_df, ratios_df if ratios_df is not None else pd.DataFrame())

    # --- 3) WACC
    wacc_res = compute_wacc(
        income_df=income_df,
        balance_df=balance_df,
        info=info,
        risk_free_rate=rf,
        equity_risk_premium=cfg.equity_risk_premium,
        rd_spread_fallback=cfg.rd_spread_fallback,
        tax_rate_fallback=cfg.tax_rate_fallback,
        current_price=float(info.get("currentPrice")) if info.get("currentPrice") is not None else None,
        shares=float(info.get("sharesOutstanding")) if info.get("sharesOutstanding") is not None else None,
    )
    wacc_res["risk_free_proxy"] = cfg.risk_free_proxy

    # --- 4) DCF
    shares = info.get("sharesOutstanding")
    if shares is None or float(shares) == 0:
        raise SystemExit("Shares outstanding missing for this ticker; cannot compute per-share DCF value.")

    dcf_res, dcf_projection = compute_dcf(
        cashflow_df=cashflow_df,
        balance_df=balance_df,
        shares=float(shares),
        current_price=float(info.get("currentPrice")) if info.get("currentPrice") is not None else None,
        wacc=float(wacc_res["wacc"]),
        projection_years=cfg.projection_years,
        terminal_growth=cfg.terminal_growth,
    )

    sens_df = sensitivity_table(
        latest_fcf=float(dcf_res["latest_fcf"]),
        growth_rate=float(dcf_res["fcf_growth_rate_clamped"]),
        projection_years=int(dcf_res["projection_years"]),
        shares=float(dcf_res["shares_outstanding"]),
        cash=float(dcf_res.get("cash", 0.0) or 0.0),
        debt=float(dcf_res.get("debt", 0.0) or 0.0),
        base_wacc=float(dcf_res["wacc"]),
        base_g=float(dcf_res["terminal_growth"]),
        wacc_deltas=cfg.wacc_deltas,
        g_deltas=cfg.g_deltas,
    )

    # --- 5) Exports (data/tables/charts)
    out_data = root / cfg.out_data
    out_tables = root / cfg.out_tables
    out_charts = root / cfg.out_charts
    out_reports = root / cfg.out_reports

    # DATA (extracted + selected)
    write_excel(income_df, out_data / "income_statement.xlsx")
    write_excel(balance_df, out_data / "balance_sheet.xlsx")
    write_excel(cashflow_df, out_data / "cashflow_statement.xlsx")
    write_kv_excel(
        {
            "symbol": symbol,
            "company_name": info.get("longName"),
            "current_price": info.get("currentPrice"),
            "market_cap": info.get("marketCap"),
            "shares_outstanding": info.get("sharesOutstanding"),
            "beta": info.get("beta"),
            "risk_free_rate": rf,
            "risk_free_proxy": cfg.risk_free_proxy,
            "data_source": "Yahoo Finance via yfinance",
        },
        out_data / "market_info.xlsx",
    )
    write_kv_excel(selected_fields, out_data / "selected_fields.xlsx")
    if isinstance(price_df, pd.DataFrame) and not price_df.empty:
        write_excel(price_df.tail(252 * 2), out_data / "price_history_last_2y.xlsx")

    # TABLES (one file per table)
    write_excel(ratios_df, out_tables / "ratios.xlsx")
    write_excel(drivers_df, out_tables / "drivers_dupont.xlsx")
    write_kv_excel(wacc_res, out_tables / "wacc.xlsx")
    write_kv_excel(dcf_res, out_tables / "dcf_summary.xlsx")
    write_excel(dcf_projection, out_tables / "dcf_projection.xlsx")
    write_excel(sens_df, out_tables / "dcf_sensitivity_table.xlsx")

    # CHARTS
    out_charts.mkdir(parents=True, exist_ok=True)
    plot_price(price_df, str(out_charts / "price_chart.png"), title=f"{symbol} Price (Adj Close)")
    plot_sensitivity_heatmap(sens_df, str(out_charts / "dcf_sensitivity_heatmap.png"), title=f"{symbol} DCF Sensitivity (Fair Value / Share)")

    # --- 6) LLM-generated investment memo (key deliverable)
    prompt = build_investment_memo_prompt(
        symbol=symbol,
        company_name=info.get("longName"),
        market_info=info,
        ratios_df=ratios_df,
        drivers_df=drivers_df,
        wacc_res=wacc_res,
        dcf_res=dcf_res,
        sensitivity_df=sens_df,
    )
    memo_md, provider_used = generate_ai_memo(
        system=prompt["system"],
        user=prompt["user"],
        provider=cfg.llm_provider,
        model=cfg.llm_model,
        ollama_base_url=cfg.ollama_base_url,
        ollama_model=cfg.ollama_model,
    )
    # stamp provider
    memo_md = memo_md + f"\n\n---\n**LLM provider used:** `{provider_used}`\n"

    save_md_html(memo_md, out_reports, basename="ai_investment_memo")

    print("\n✅ Completed. Generated outputs:")
    print(f"- data/:    {out_data}")
    print(f"- tables/:  {out_tables}")
    print(f"- charts/:  {out_charts}")
    print(f"- reports/: {out_reports}")
    print(f"  - reports/ai_investment_memo.md + .html (LLM: {provider_used})")

if __name__ == "__main__":
    main()
