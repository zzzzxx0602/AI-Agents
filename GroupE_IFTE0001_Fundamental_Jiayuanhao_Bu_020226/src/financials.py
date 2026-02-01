import pandas as pd
from .utils import safe_loc, normalize_year_index

def build_income_statement(income_raw, quarterly_raw=None) -> pd.DataFrame:
    income_df = pd.DataFrame()
    income_df["Total Revenue"] = safe_loc(income_raw, "Total Revenue")
    income_df["Cost of Revenue"] = safe_loc(income_raw, "Cost Of Revenue")
    income_df["Net Income"] = safe_loc(income_raw, "Net Income")

    income_df = normalize_year_index(income_df)

    # TTM from quarterly (if available)
    if quarterly_raw is not None and not getattr(quarterly_raw, "empty", True):
        q_rev = safe_loc(quarterly_raw, "Total Revenue")
        q_cost = safe_loc(quarterly_raw, "Cost Of Revenue")
        q_net = safe_loc(quarterly_raw, "Net Income")

        def ttm(series):
            s = series.dropna()
            if len(s) >= 4:
                return series.iloc[:4].sum()
            return None

        ttm_rev, ttm_cost, ttm_net = ttm(q_rev), ttm(q_cost), ttm(q_net)
        if any(v is not None for v in [ttm_rev, ttm_cost, ttm_net]):
            income_df.loc["TTM"] = [ttm_rev, ttm_cost, ttm_net]

    income_df = income_df.sort_index()
    income_df = income_df.apply(pd.to_numeric, errors="coerce")
    return income_df

def build_balance_sheet(balance_raw) -> pd.DataFrame:
    balance_df = pd.DataFrame()
    balance_df["Total Assets"] = safe_loc(balance_raw, "Total Assets")
    balance_df["Total Debt"] = safe_loc(balance_raw, "Total Debt")
    balance_df["Shareholders' Equity"] = safe_loc(balance_raw, "Stockholders Equity")

    balance_df = normalize_year_index(balance_df)
    balance_df = balance_df.sort_index()
    balance_df = balance_df.apply(pd.to_numeric, errors="coerce")
    return balance_df
