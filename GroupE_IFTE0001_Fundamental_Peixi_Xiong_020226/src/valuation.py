from __future__ import annotations
import numpy as np
import pandas as pd
from .data import pick_col

def compute_wacc(
    income_df: pd.DataFrame,
    balance_df: pd.DataFrame,
    info: dict,
    risk_free_rate: float,
    equity_risk_premium: float,
    rd_spread_fallback: float,
    tax_rate_fallback: float,
    current_price: float | None,
    shares: float | None,
) -> dict:
    beta = info.get("beta", 1.1) or 1.1
    cost_of_equity = risk_free_rate + float(beta) * float(equity_risk_premium)

    debt_cols = [
        "Total Debt",
        "Long Term Debt",
        "Long Term Debt And Capital Lease Obligation",
        "Short Long Term Debt",
        "Short/Current Long Term Debt",
    ]
    debt_col = pick_col(balance_df, debt_cols)
    total_debt = float(balance_df[debt_col].dropna().iloc[-1]) if debt_col is not None and not balance_df.empty else 0.0

    # Cost of debt: interest expense / debt if possible, else rf + spread
    pre_tax_rd = float(risk_free_rate) + float(rd_spread_fallback)
    int_col = pick_col(income_df, ["Interest Expense", "InterestExpense"])
    if int_col is not None and total_debt > 0 and not income_df.empty:
        try:
            interest_expense = abs(float(income_df[int_col].dropna().iloc[-1]))
            if interest_expense > 0:
                pre_tax_rd = min(max(interest_expense / total_debt, 0.0), 0.20)
        except Exception:
            pass

    # Effective tax rate
    tax_col = pick_col(income_df, ["Tax Provision", "Income Tax Expense", "Provision for Income Taxes"])
    pretax_col = pick_col(income_df, ["Pretax Income", "Income Before Tax", "Earnings Before Tax"])
    eff_tax_rate = float(tax_rate_fallback)
    if tax_col is not None and pretax_col is not None and not income_df.empty:
        try:
            tax = float(income_df[tax_col].dropna().iloc[-1])
            pretax = float(income_df[pretax_col].dropna().iloc[-1])
            if pretax != 0:
                eff_tax_rate = float(np.clip(tax / pretax, 0.0, 0.25))
        except Exception:
            pass

    # Market cap proxy
    m_cap = info.get("marketCap")
    if m_cap is None:
        if current_price is not None and shares is not None:
            m_cap = float(current_price) * float(shares)
        else:
            m_cap = 0.0

    total_capital = float(m_cap) + float(total_debt)
    if total_capital <= 0:
        w_e, w_d = 1.0, 0.0
        wacc = 0.09
    else:
        w_e = float(m_cap) / total_capital
        w_d = float(total_debt) / total_capital
        wacc = (w_e * cost_of_equity) + (w_d * pre_tax_rd * (1 - eff_tax_rate))

    return {
        "risk_free_rate": float(risk_free_rate),
        "beta": float(beta),
        "equity_risk_premium": float(equity_risk_premium),
        "cost_of_equity": float(cost_of_equity),
        "total_debt": float(total_debt),
        "debt_field": debt_col,
        "pre_tax_cost_of_debt": float(pre_tax_rd),
        "effective_tax_rate": float(eff_tax_rate),
        "equity_weight": float(w_e),
        "debt_weight": float(w_d),
        "wacc": float(wacc),
        "market_cap": float(m_cap),
    }

def compute_dcf(
    cashflow_df: pd.DataFrame,
    balance_df: pd.DataFrame,
    shares: float,
    current_price: float | None,
    wacc: float,
    projection_years: int,
    terminal_growth: float,
) -> tuple[dict, pd.DataFrame]:
    ocf_col = pick_col(cashflow_df, ["Total Cash From Operating Activities", "Operating Cash Flow"])
    capex_col = pick_col(cashflow_df, ["Capital Expenditures", "Capital Expenditure"])
    if ocf_col is None or capex_col is None:
        raise KeyError("Cashflow missing OCF or CapEx line items.")

    fcf_series = (cashflow_df[ocf_col] - cashflow_df[capex_col].abs()).dropna().sort_index()
    if fcf_series.shape[0] < 2:
        raise ValueError("Not enough historical cashflow years to estimate FCF trend.")

    latest_fcf = float(fcf_series.iloc[-1])
    first_fcf = float(fcf_series.iloc[0])
    n_years = fcf_series.shape[0] - 1
    if first_fcf > 0 and latest_fcf > 0 and n_years > 0:
        fcf_cagr = (latest_fcf / first_fcf) ** (1 / n_years) - 1
    else:
        fcf_cagr = 0.05
    growth_rate = float(np.clip(fcf_cagr, -0.05, 0.15))

    g_terminal = float(terminal_growth)
    if g_terminal >= (wacc - 0.005):
        g_terminal = max(0.01, wacc - 0.02)

    rows = []
    disc_sum = 0.0
    last_fcf = None
    for t in range(1, projection_years + 1):
        fcf_t = latest_fcf * ((1 + growth_rate) ** t)
        disc = fcf_t / ((1 + wacc) ** t)
        disc_sum += disc
        last_fcf = fcf_t
        rows.append({"year": t, "fcf": fcf_t, "discounted_fcf": disc})

    terminal_fcf = last_fcf * (1 + g_terminal)
    terminal_value = terminal_fcf / (wacc - g_terminal)
    discounted_tv = terminal_value / ((1 + wacc) ** projection_years)
    enterprise_value = float(disc_sum + discounted_tv)

    cash_col = pick_col(balance_df, [
        "Cash And Cash Equivalents",
        "Cash Cash Equivalents And Short Term Investments",
        "Cash And Short Term Investments"
    ])
    debt_col = pick_col(balance_df, [
        "Total Debt",
        "Long Term Debt",
        "Long Term Debt And Capital Lease Obligation",
        "Short Long Term Debt"
    ])

    cash = float(balance_df[cash_col].dropna().iloc[-1]) if cash_col is not None and not balance_df.empty else 0.0
    debt = float(balance_df[debt_col].dropna().iloc[-1]) if debt_col is not None and not balance_df.empty else 0.0

    equity_value = enterprise_value - debt + cash
    fair_value_per_share = equity_value / float(shares)
    upside = None
    if current_price is not None and current_price != 0:
        upside = float(fair_value_per_share / float(current_price) - 1)

    dcf_result = {
        "method": "FCF-based DCF (5Y projection + terminal value, net debt adjusted)",
        "historical_fcf_years_used": [int(x) for x in fcf_series.index.year],
        "latest_fcf": latest_fcf,
        "fcf_growth_rate_clamped": growth_rate,
        "wacc": float(wacc),
        "terminal_growth": float(g_terminal),
        "projection_years": int(projection_years),
        "enterprise_value": enterprise_value,
        "cash": cash,
        "debt": debt,
        "equity_value": equity_value,
        "shares_outstanding": float(shares),
        "fair_value_per_share": float(fair_value_per_share),
        "current_price": float(current_price) if current_price is not None else None,
        "upside_vs_current_price": upside,
        "cash_field": cash_col,
        "debt_field": debt_col,
    }

    proj_df = pd.DataFrame(rows)
    proj_df["terminal_value"] = np.nan
    proj_df.loc[proj_df.index.max(), "terminal_value"] = terminal_value
    proj_df["discounted_terminal_value"] = np.nan
    proj_df.loc[proj_df.index.max(), "discounted_terminal_value"] = discounted_tv
    return dcf_result, proj_df

def sensitivity_table(
    latest_fcf: float,
    growth_rate: float,
    projection_years: int,
    shares: float,
    cash: float,
    debt: float,
    base_wacc: float,
    base_g: float,
    wacc_deltas: tuple[float, ...],
    g_deltas: tuple[float, ...],
) -> pd.DataFrame:
    def fv_per_share(wacc: float, g: float) -> float:
        if shares == 0 or g >= (wacc - 0.005):
            return np.nan
        disc_sum = 0.0
        last = None
        for t in range(1, projection_years + 1):
            fcf_t = latest_fcf * ((1 + growth_rate) ** t)
            disc_sum += fcf_t / ((1 + wacc) ** t)
            last = fcf_t
        tv = (last * (1 + g)) / (wacc - g)
        disc_tv = tv / ((1 + wacc) ** projection_years)
        ev = disc_sum + disc_tv
        eq = ev - debt + cash
        return eq / shares

    w_list = sorted([base_wacc + d for d in wacc_deltas])
    g_list = sorted([base_g + d for d in g_deltas], reverse=True)

    mat = []
    for g in g_list:
        row = []
        for w in w_list:
            row.append(fv_per_share(float(w), float(g)))
        mat.append(row)

    return pd.DataFrame(mat, index=[f"g={g:.2%}" for g in g_list], columns=[f"WACC={w:.2%}" for w in w_list])
