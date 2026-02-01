from pathlib import Path

from src.agent import FinancialAnalysisAgent
from src.report import render_report_html, render_trade_note_html
from src.memo import generate_investment_memo, save_memo


def main():
    # Make outputs path deterministic even if the IDE sets a different working directory.
    project_root = Path(__file__).resolve().parent
    outputs_dir = project_root / "reports"
    outputs_dir.mkdir(exist_ok=True)

    ticker = "AMZN"
    agent = FinancialAnalysisAgent()

    # Run the full agent workflow (tables + ratios + valuation + charts)
    outputs = agent.run(ticker=ticker, outputs_dir=str(outputs_dir), make_charts=True)

    print("\n=== AI Financial Analysis Agent Demo (Key Outputs) ===\n")
    print("Project root:", project_root)
    print("Outputs folder:", outputs_dir)
    print("Ticker:", ticker)
    print("Income Statement shape:", outputs.income_statement.shape)
    print("Balance Sheet shape:", outputs.balance_sheet.shape)

    print("\nKey Ratios (latest):")
    try:
        print("Gross Margin:", float(outputs.gross_margin.dropna().iloc[-1, 0]))
    except Exception:
        print("Gross Margin: N/A")
    try:
        print("ROE:", float(outputs.roe.dropna().iloc[-1, 0]))
    except Exception:
        print("ROE: N/A")
    try:
        print("Debt-to-Equity:", float(outputs.debt_to_equity.dropna().iloc[-1, 0]))
    except Exception:
        print("Debt-to-Equity: N/A")
    try:
        print("Asset Turnover:", float(outputs.asset_turnover.dropna().iloc[-1, 0]))
    except Exception:
        print("Asset Turnover: N/A")

    print("\nAltman Z-score:")
    print(outputs.altman_table)

    if outputs.pe_summary.get("pe_ttm") is not None:
        print("\nP/E (TTM):", outputs.pe_summary.get("pe_ttm"))
        print("Dynamic red-line:", outputs.pe_summary.get("dynamic_redline"))
        print("Result:", outputs.pe_summary.get("pe_result"))
    else:
        print("\nP/E data not available from Yahoo for this ticker right now.")

    print("\nDCF Equity Value (approx):", f"{outputs.dcf_summary['dcf_equity_value']:,.0f}")

    # ---- Investment Memo (deterministic, aligned to my HTML memo structure) ----
    memo_text = generate_investment_memo(ticker, outputs)
    memo_path = save_memo(memo_text, outputs_dir=str(outputs_dir), ticker=ticker)
    print("\n[OK] Generated Investment Memo:", memo_path)
    print("[TIP] Open it directly: ", Path(memo_path).resolve())

    # ---- Single HTML report that embeds tables + valuation + memo reference ----
    report_path = render_report_html(ticker, outputs, outputs_dir=str(outputs_dir), memo_path=memo_path)
    print("\n[OK] Saved outputs to:", outputs_dir)
    print("[OK] Generated HTML report (open manually):", report_path)

    # ---- Teammate-style Trade Note HTML (single file, like sample) ----
    trade_note_path = render_trade_note_html(ticker, outputs, outputs_dir=str(outputs_dir), memo_path=memo_path)
    print("[OK] Generated Trade Note HTML (open manually):", trade_note_path)



if __name__ == "__main__":
    main()
