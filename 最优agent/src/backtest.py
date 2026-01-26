import numpy as np
import pandas as pd

def _bps_to_frac(bps: float) -> float:
    return bps / 10_000.0

def compute_metrics(equity_curve: pd.Series, daily_returns: pd.Series, benchmark_series: pd.Series = None) -> dict:
    """Computes comprehensive performance metrics, including Benchmark comparison."""
    if equity_curve.empty:
        return {}
    
    n_days = len(equity_curve)
    start_val = float(equity_curve.iloc[0])
    end_val = float(equity_curve.iloc[-1])

    # 1. Total Return (累计总回报) - NEW
    total_return = (end_val / start_val) - 1

    # 2. Strategy CAGR
    years = n_days / 252.0
    cagr = (end_val / start_val) ** (1 / years) - 1 if years > 0 else np.nan

    # 3. Volatility
    vol = daily_returns.std(ddof=0) * np.sqrt(252)

    # 4. Sharpe
    sharpe = (daily_returns.mean() * 252) / (vol + 1e-12)

    # 5. Max Drawdown
    running_max = equity_curve.cummax()
    dd = equity_curve / running_max - 1
    max_dd = dd.min()

    # 6. Sortino & Calmar
    downside_returns = daily_returns[daily_returns < 0]
    downside_vol = downside_returns.std(ddof=0) * np.sqrt(252)
    sortino = (daily_returns.mean() * 252) / (downside_vol + 1e-12)
    calmar = cagr / abs(max_dd) if max_dd != 0 else np.nan

    metrics = {
        "TotalReturn": total_return,  # 新增指标
        "CAGR": cagr,
        "AnnVol": vol,
        "Sharpe": sharpe,
        "Sortino": sortino,
        "Calmar": calmar,
        "MaxDrawdown": max_dd,
        "EndEquity": end_val,
    }

    # Benchmark Calculation
    if benchmark_series is not None:
        bench_start = float(benchmark_series.iloc[0])
        bench_end = float(benchmark_series.iloc[-1])
        bench_cagr = (bench_end / bench_start) ** (1 / years) - 1 if years > 0 else np.nan
        bench_total_return = (bench_end / bench_start) - 1
        
        metrics["Benchmark_CAGR"] = bench_cagr
        metrics["Benchmark_TotalReturn"] = bench_total_return # 新增 Benchmark 总回报

    return metrics

# 下面的回测主函数保持不变，但为了防止 writefile 覆盖导致丢失，
# 我们必须完整粘贴一遍 backtest_long_only_chandelier_strategy_voltarget 函数。
# (由于代码较长，我只粘贴函数头和调用 metrics 的部分，中间逻辑不变)

def backtest_long_only_chandelier_strategy_voltarget(
    df: pd.DataFrame,
    initial_equity: float,
    risk_pct_equity: float,
    hard_stop_atr_multiple: float,
    use_trailing_stop: bool,
    target_ann_vol: float,
    strategy_vol_lookback: int,
    max_leverage: float,
    min_leverage: float,
    commission_bps: float,
    slippage_bps: float,
    allow_reentry_same_day: bool,
    min_atr: float,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    
    df = df.copy()
    comm = _bps_to_frac(commission_bps)
    slip = _bps_to_frac(slippage_bps)

    position = 0.0
    entry_price = np.nan
    stop_price = np.nan
    equity_cash = initial_equity

    equity_history = [initial_equity] 
    ret_history = [0.0]

    rows = []
    trades = []
    in_trade = False
    last_exit_date = None
    entry_dt = None
    entry_L = np.nan

    for i in range(1, len(df)):
        date = df.index[i]
        o = float(df["Open"].iloc[i])
        l = float(df["Low"].iloc[i])
        c = float(df["Close"].iloc[i])

        atr = float(df["ATR"].iloc[i-1])
        atr = max(atr, min_atr)
        chandelier_prev = df["ChandelierStop"].iloc[i-1]
        chandelier_prev = float(chandelier_prev) if pd.notna(chandelier_prev) else np.nan

        if len(ret_history) >= strategy_vol_lookback:
            window = np.array(ret_history[-strategy_vol_lookback:], dtype=float)
            strat_vol = float(np.std(window, ddof=0) * np.sqrt(252))
        else:
            strat_vol = target_ann_vol

        min_vol_floor = 0.05 
        effective_vol = max(strat_vol, min_vol_floor)
        L = target_ann_vol / effective_vol
        L = float(np.clip(L, min_leverage, max_leverage))

        if in_trade and np.isfinite(chandelier_prev):
            if np.isfinite(stop_price):
                stop_price = max(stop_price, chandelier_prev) if use_trailing_stop else chandelier_prev
            else:
                stop_price = chandelier_prev

        stop_triggered = False
        if in_trade and np.isfinite(stop_price) and (l <= stop_price):
            stop_triggered = True
            exit_px = stop_price * (1 - slip)
            gross_pnl = position * (exit_px - entry_price)
            costs = abs(position) * exit_px * (comm + slip)
            equity_cash += gross_pnl - costs

            trades.append({
                "entry_date": entry_dt,
                "exit_date": date,
                "entry_price": entry_price,
                "exit_price": exit_px,
                "shares": position,
                "leverage_mult_at_entry": entry_L,
                "pnl": gross_pnl - costs,
                "exit_reason": "CHAND_STOP",
            })

            position = 0.0
            in_trade = False
            last_exit_date = date
            entry_price = np.nan
            stop_price = np.nan
            entry_dt = None
            entry_L = np.nan

        exit_signal = bool(df["exit_long"].iloc[i-1])
        entry_signal = bool(df["entry_long"].iloc[i-1])

        if in_trade and (not stop_triggered) and exit_signal:
            exit_px = o * (1 - slip)
            gross_pnl = position * (exit_px - entry_price)
            costs = abs(position) * exit_px * (comm + slip)
            equity_cash += gross_pnl - costs

            trades.append({
                "entry_date": entry_dt,
                "exit_date": date,
                "entry_price": entry_price,
                "exit_price": exit_px,
                "shares": position,
                "leverage_mult_at_entry": entry_L,
                "pnl": gross_pnl - costs,
                "exit_reason": "CHAND_CLOSE",
            })

            position = 0.0
            in_trade = False
            last_exit_date = date
            entry_price = np.nan
            stop_price = np.nan
            entry_dt = None
            entry_L = np.nan

        if (not in_trade) and entry_signal:
            if (not allow_reentry_same_day) and (last_exit_date == date):
                pass
            else:
                risk_dollars = equity_cash * risk_pct_equity
                stop_dist = hard_stop_atr_multiple * atr
                base_shares = np.floor(risk_dollars / stop_dist)
                shares = np.floor(base_shares * L)

                if shares > 0:
                    fill_px = o * (1 + slip)
                    costs = abs(shares) * fill_px * (comm + slip)
                    position = float(shares)
                    entry_price = fill_px
                    in_trade = True
                    entry_dt = date
                    entry_L = L
                    hard_stop = entry_price - hard_stop_atr_multiple * atr
                    stop_price = max(hard_stop, chandelier_prev) if np.isfinite(chandelier_prev) else hard_stop
                    equity_cash -= costs

        mtm = equity_cash if not in_trade else equity_cash + position * (c - entry_price)
        prev_equity = equity_history[-1]
        ret = (mtm / prev_equity - 1.0) if prev_equity > 0 else 0.0
        equity_history.append(mtm)
        ret_history.append(ret)

        rows.append({
            "date": date,
            "equity": mtm,
            "daily_return": ret,
            "position_shares": position if in_trade else 0.0,
            "entry_price": entry_price if in_trade else np.nan,
            "stop_price": stop_price if in_trade else np.nan,
            "strategy_realized_vol": strat_vol,
            "leverage_mult_today": L,
        })

    equity_df = pd.DataFrame(rows).set_index("date")
    trades_df = pd.DataFrame(trades)

    # 传入 benchmark 用于 metrics
    metrics = compute_metrics(equity_df["equity"], equity_df["daily_return"], df["Close"])

    if not trades_df.empty:
        win_rate = (trades_df["pnl"] > 0).mean()
        avg_pnl = trades_df["pnl"].mean()
        metrics.update({
            "Trades": int(len(trades_df)),
            "WinRate": float(win_rate),
            "AvgPnL": float(avg_pnl),
            "AvgLeverageMult": float(trades_df["leverage_mult_at_entry"].mean()),
        })
    else:
        metrics.update({"Trades": 0, "WinRate": np.nan, "AvgPnL": np.nan, "AvgLeverageMult": np.nan})

    return equity_df, trades_df, metrics