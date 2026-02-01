from __future__ import annotations
import numpy as np
import pandas as pd
from .data import pick_col

def compute_core_ratios(income_df: pd.DataFrame, balance_df: pd.DataFrame, cashflow_df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    ratios_df = pd.DataFrame(index=income_df.index)
    meta = {}

    rev_col = pick_col(income_df, ["Total Revenue", "TotalRevenue", "Revenue"])
    gp_col  = pick_col(income_df, ["Gross Profit", "GrossProfit"])
    op_col  = pick_col(income_df, ["Operating Income", "OperatingIncome"])
    ni_col  = pick_col(income_df, ["Net Income", "NetIncome"])

    equity_col = pick_col(balance_df, ["Stockholders Equity", "Total Stockholder Equity", "Total Equity Gross Minority Interest"])
    assets_col = pick_col(balance_df, ["Total Assets", "TotalAssets"])
    curr_assets_col = pick_col(balance_df, ["Current Assets", "Total Current Assets"])
    curr_liab_col   = pick_col(balance_df, ["Current Liabilities", "Total Current Liabilities"])
    liab_col        = pick_col(balance_df, ["Total Liabilities Net Minority Interest", "Total Liab", "TotalLiab"])

    ocf_col = pick_col(cashflow_df, ["Total Cash From Operating Activities", "Operating Cash Flow"])
    capex_col = pick_col(cashflow_df, ["Capital Expenditures", "Capital Expenditure"])

    meta.update({
        "Revenue column used": rev_col,
        "Gross Profit column used": gp_col,
        "Operating Income column used": op_col,
        "Net Income column used": ni_col,
        "Total Assets column used": assets_col,
        "Equity column used": equity_col,
        "Total Liabilities column used": liab_col,
        "OCF column used": ocf_col,
        "CapEx column used": capex_col,
    })

    if rev_col is None or ni_col is None:
        return pd.DataFrame(), meta

    # Profitability
    if gp_col is not None:
        ratios_df["Profitability: Gross Margin"] = income_df[gp_col] / income_df[rev_col]
    if op_col is not None:
        ratios_df["Profitability: Operating Margin"] = income_df[op_col] / income_df[rev_col]
    ratios_df["Profitability: Net Margin"] = income_df[ni_col] / income_df[rev_col]

    # Efficiency
    if assets_col is not None and not balance_df.empty:
        ratios_df["Efficiency: Asset Turnover"] = income_df[rev_col] / balance_df[assets_col]
    if equity_col is not None and not balance_df.empty:
        ratios_df["Efficiency: ROE"] = income_df[ni_col] / balance_df[equity_col]

    # Leverage / Liquidity
    if liab_col is not None and assets_col is not None and not balance_df.empty:
        ratios_df["Leverage: Debt to Assets"] = balance_df[liab_col] / balance_df[assets_col]
    if curr_assets_col is not None and curr_liab_col is not None and not balance_df.empty:
        ratios_df["Liquidity: Current Ratio"] = balance_df[curr_assets_col] / balance_df[curr_liab_col]

    # Growth
    rev_series = income_df[rev_col].sort_index()
    ratios_df["Growth: Revenue YoY"] = rev_series.pct_change()
    if rev_series.dropna().shape[0] >= 2 and (rev_series.dropna().iloc[0] > 0):
        n_years = rev_series.dropna().shape[0] - 1
        cagr = (rev_series.dropna().iloc[-1] / rev_series.dropna().iloc[0]) ** (1 / n_years) - 1
    else:
        cagr = np.nan
    ratios_df["Growth: Revenue CAGR (period)"] = cagr

    # Quality
    if ocf_col is not None:
        ratios_df["Quality: OCF / Net Income"] = cashflow_df[ocf_col] / income_df[ni_col]
    if ocf_col is not None and capex_col is not None:
        fcf = cashflow_df[ocf_col] - cashflow_df[capex_col].abs()
        ratios_df["Quality: FCF Margin"] = fcf / income_df[rev_col]

    return ratios_df, meta

def compute_drivers(income_df: pd.DataFrame, balance_df: pd.DataFrame, ratios_df: pd.DataFrame) -> pd.DataFrame:
    drivers_df = pd.DataFrame(index=income_df.index)

    rev_col = pick_col(income_df, ["Total Revenue", "TotalRevenue", "Revenue"])
    assets_col = pick_col(balance_df, ["Total Assets", "TotalAssets"])
    equity_col = pick_col(balance_df, ["Stockholders Equity", "Total Stockholder Equity", "Total Equity Gross Minority Interest"])

    if rev_col is not None:
        rev_series = income_df[rev_col].sort_index()
        drivers_df["Revenue Growth (YoY)"] = rev_series.pct_change()

    # DuPont (ROE ≈ NetMargin × AssetTurnover × EquityMultiplier)
    if "Profitability: Net Margin" in ratios_df.columns:
        drivers_df["DuPont: Net Margin"] = ratios_df["Profitability: Net Margin"]
    if "Efficiency: Asset Turnover" in ratios_df.columns:
        drivers_df["DuPont: Asset Turnover"] = ratios_df["Efficiency: Asset Turnover"]
    if assets_col is not None and equity_col is not None and not balance_df.empty:
        drivers_df["DuPont: Equity Multiplier"] = balance_df[assets_col] / balance_df[equity_col]

    return drivers_df
