# src/metrics.py
from __future__ import annotations

import numpy as np
import pandas as pd

ANN = 252


def total_return(equity: pd.Series) -> float:
    equity = equity.dropna()
    if len(equity) < 2:
        return np.nan
    return float(equity.iloc[-1] / equity.iloc[0] - 1.0)


def cagr(equity: pd.Series) -> float:
    equity = equity.dropna()
    if len(equity) < 2:
        return np.nan

    years = (equity.index[-1] - equity.index[0]).days / 365.25
    if years <= 0:
        return np.nan

    return float((equity.iloc[-1] / equity.iloc[0]) ** (1.0 / years) - 1.0)


def max_drawdown(equity: pd.Series) -> float:
    equity = equity.dropna()
    if len(equity) < 2:
        return np.nan
    peak = equity.cummax()
    dd = equity / peak - 1.0
    return float(dd.min())


def _annual_to_daily_rf(rf_annual: float, periods: int = ANN) -> float:
    """
    Convert annual risk-free rate to daily using geometric conversion:
      rf_daily = (1 + rf_annual)^(1/periods) - 1
    """
    rf_annual = float(rf_annual)
    periods = float(periods)
    return (1.0 + rf_annual) ** (1.0 / periods) - 1.0


def sharpe_ratio(
    daily_ret: pd.Series,
    rf_annual: float = 0.0,
    periods: int = ANN,
) -> float:
    """
    Annualized Sharpe Ratio with risk-free rate:
      Sharpe = mean(excess_daily_ret) / std(daily_ret) * sqrt(periods)

    excess_daily_ret = daily_ret - rf_daily
    rf_daily = (1 + rf_annual)^(1/periods) - 1
    """
    r = daily_ret.dropna()
    if len(r) < 2:
        return np.nan

    vol = r.std()
    if vol == 0 or np.isnan(vol):
        return np.nan

    rf_daily = _annual_to_daily_rf(rf_annual, periods=periods)
    excess = r - rf_daily

    return float((excess.mean() / vol) * np.sqrt(periods))


def hit_rate_on_rebalances(df: pd.DataFrame) -> float:
    """
    Win rate defined on rebalance events:
    - Find days where trade_flag == 1
    - Evaluate NEXT day's strategy return (>0)
    """
    if "trade_flag" not in df.columns or "strategy_ret" not in df.columns:
        return np.nan

    trade_days = df.index[df["trade_flag"] == 1]
    if len(trade_days) == 0:
        return np.nan

    next_ret = df.loc[trade_days, "strategy_ret"].shift(-1).dropna()
    if len(next_ret) == 0:
        return np.nan

    return float((next_ret > 0).mean())
