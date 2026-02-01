import yfinance as yf
import pandas as pd

def safe_loc(df, row):
    if df is None or getattr(df, "empty", True) or row not in df.index:
        return None
    return df.loc[row]

def compute_historical_cagr(series: pd.Series, years: int = 3) -> float:
    s = series.dropna()
    if len(s) < years + 1:
        return 0.05
    start = s.iloc[years]
    end = s.iloc[0]
    return (end / start) ** (1 / years) - 1

def minimal_dcf(ticker: str = "AMZN", years: int = 5):
    stock = yf.Ticker(ticker)
    financials = stock.financials
    quarterly = stock.quarterly_financials

    annual_revenue = safe_loc(financials, "Total Revenue")
    annual_net_income = safe_loc(financials, "Net Income")

    q_rev = safe_loc(quarterly, "Total Revenue")
    q_net = safe_loc(quarterly, "Net Income")

    if q_rev is not None and len(q_rev.dropna()) >= 4:
        ttm_revenue = q_rev.iloc[:4].sum()
    else:
        ttm_revenue = annual_revenue.iloc[0]

    if q_net is not None and len(q_net.dropna()) >= 4:
        ttm_net_income = q_net.iloc[:4].sum()
    else:
        ttm_net_income = annual_net_income.iloc[0]

    margin = ttm_net_income / ttm_revenue

    historical_growth = compute_historical_cagr(annual_revenue, years=3)
    growth_rate = min(max(historical_growth, 0.02), 0.15)

    beta = stock.info.get("beta", 1.2)
    risk_free_rate = 0.04
    market_premium = 0.055
    discount_rate = risk_free_rate + beta * market_premium

    terminal_growth = min(max(historical_growth / 2, 0.01), 0.04)

    forecast = []
    for t in range(1, years + 1):
        revenue_t = ttm_revenue * (1 + growth_rate) ** t
        net_income_t = revenue_t * margin
        forecast.append(net_income_t)

    forecast = pd.Series(forecast, index=[f"Year {i}" for i in range(1, years + 1)])

    discount_factors = [(1 / (1 + discount_rate) ** t) for t in range(1, years + 1)]
    pv_cf = forecast.values * discount_factors

    terminal_value = forecast.iloc[-1] * (1 + terminal_growth) / (discount_rate - terminal_growth)
    pv_terminal = terminal_value / (1 + discount_rate) ** years
    dcf_equity_value = pv_cf.sum() + pv_terminal

    return {
        "ttm_revenue": float(ttm_revenue),
        "ttm_net_income": float(ttm_net_income),
        "margin": float(margin),
        "growth_rate": float(growth_rate),
        "discount_rate": float(discount_rate),
        "terminal_growth": float(terminal_growth),
        "years": years,
        "forecast_net_income": forecast,
        "terminal_value": float(terminal_value),
        "pv_terminal": float(pv_terminal),
        "dcf_equity_value": float(dcf_equity_value),
    }
