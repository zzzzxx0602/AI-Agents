import os
from dataclasses import dataclass
import pandas as pd

from .data import fetch_statements
from .financials import build_income_statement, build_balance_sheet
from .ratios import compute_ratios, plot_ratio
from .altman import build_financial_dataframe, compute_altman_z_score, classify_z_score
from .pe import get_pe_ttm_from_yahoo, compute_dynamic_pe_redline, pe_valuation_check
from .dcf import minimal_dcf

@dataclass
class AgentOutputs:
    income_statement: pd.DataFrame
    balance_sheet: pd.DataFrame
    gross_margin: pd.DataFrame
    roe: pd.DataFrame
    debt_to_equity: pd.DataFrame
    asset_turnover: pd.DataFrame
    altman_table: pd.DataFrame
    pe_summary: dict
    dcf_summary: dict

class FinancialAnalysisAgent:
    """Runs your workflow: statements -> ratios -> Altman Z -> P/E check -> minimal DCF."""

    def run(self, ticker: str = "AMZN", outputs_dir: str = "outputs", make_charts: bool = True) -> AgentOutputs:
        os.makedirs(outputs_dir, exist_ok=True)

        _, income_raw, balance_raw, quarterly_raw = fetch_statements(ticker)

        income_df = build_income_statement(income_raw, quarterly_raw)
        balance_df = build_balance_sheet(balance_raw)

        gm, roe, de, at = compute_ratios(income_df, balance_df)

        zdf = build_financial_dataframe(ticker)
        zdf["Altman_Z_Score"] = compute_altman_z_score(zdf)
        zdf["Financial_Risk_Zone"] = zdf["Altman_Z_Score"].apply(classify_z_score)
        altman_table = zdf[["Altman_Z_Score", "Financial_Risk_Zone"]].copy()

        pe_ttm = get_pe_ttm_from_yahoo(ticker)
        redline_result = compute_dynamic_pe_redline(ticker)
        pe_summary = {"ticker": ticker, "pe_ttm": pe_ttm, "dynamic_redline": None, "peer_median_pe": None, "pe_result": None, "assessment": None}
        if pe_ttm is not None and redline_result is not None:
            dynamic_redline, peer_median_pe, peer_pes = redline_result
            result, assessment = pe_valuation_check(pe_ttm, dynamic_redline)
            pe_summary.update({
                "dynamic_redline": dynamic_redline,
                "peer_median_pe": peer_median_pe,
                "peer_pes": peer_pes,
                "pe_result": result,
                "assessment": assessment
            })

        dcf_summary = minimal_dcf(ticker)

        income_df.to_csv(os.path.join(outputs_dir, f"{ticker}_income_statement.csv"))
        balance_df.to_csv(os.path.join(outputs_dir, f"{ticker}_balance_sheet.csv"))
        altman_table.to_csv(os.path.join(outputs_dir, f"{ticker}_altman_zscore.csv"))

        gm.to_csv(os.path.join(outputs_dir, f"{ticker}_gross_margin.csv"))
        roe.to_csv(os.path.join(outputs_dir, f"{ticker}_roe.csv"))
        de.to_csv(os.path.join(outputs_dir, f"{ticker}_debt_to_equity.csv"))
        at.to_csv(os.path.join(outputs_dir, f"{ticker}_asset_turnover.csv"))

        if make_charts:
            plot_ratio(gm.dropna(), "Gross Margin Trend", "Gross Margin", os.path.join(outputs_dir, f"{ticker}_gross_margin_trend.png"))
            plot_ratio(roe.dropna(), "ROE Trend", "ROE", os.path.join(outputs_dir, f"{ticker}_roe_trend.png"))
            plot_ratio(de.dropna(), "Debt-to-Equity Ratio Trend", "D/E Ratio", os.path.join(outputs_dir, f"{ticker}_de_trend.png"))
            plot_ratio(at.dropna(), "Asset Turnover Trend", "Asset Turnover", os.path.join(outputs_dir, f"{ticker}_asset_turnover_trend.png"))

        return AgentOutputs(
            income_statement=income_df,
            balance_sheet=balance_df,
            gross_margin=gm,
            roe=roe,
            debt_to_equity=de,
            asset_turnover=at,
            altman_table=altman_table,
            pe_summary=pe_summary,
            dcf_summary=dcf_summary
        )
