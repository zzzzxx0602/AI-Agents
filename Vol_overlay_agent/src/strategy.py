# src/strategy.py
from __future__ import annotations

import numpy as np
import pandas as pd

ANN = 252


# ------------------------------------------------------------
# 1) Legacy: single-indicator vol targeting overlay
# ------------------------------------------------------------
def compute_vol_target_overlay(
    df: pd.DataFrame,
    window_days: int = 20,
    target_vol: float = 0.20,
    min_exposure: float = 0.0,
    max_exposure: float = 1.0,
    rebalance_threshold: float = 0.05,
) -> pd.DataFrame:
    """
    Backward-compatible: simple vol targeting overlay with thresholded execution.
    NOTE: Uses log returns (legacy behavior).
    """
    df = df.copy()

    df["ret"] = np.log(df["Close"]).diff()
    df["vol"] = df["ret"].rolling(window_days).std() * np.sqrt(ANN)

    df["exposure_raw"] = target_vol / df["vol"]
    df["exposure_target"] = df["exposure_raw"].clip(lower=min_exposure, upper=max_exposure)

    exec_exposure = []
    last_exec = np.nan
    for x in df["exposure_target"].values:
        if np.isnan(x):
            exec_exposure.append(np.nan)
            continue
        if np.isnan(last_exec):
            last_exec = x
            exec_exposure.append(last_exec)
            continue
        if abs(x - last_exec) >= rebalance_threshold:
            last_exec = x
        exec_exposure.append(last_exec)

    df["exposure"] = pd.Series(exec_exposure, index=df.index).clip(min_exposure, max_exposure)

    df["strategy_ret"] = df["exposure"].shift(1) * df["ret"]
    df["bh_ret"] = df["ret"]

    df["strategy_equity"] = (1 + df["strategy_ret"].fillna(0)).cumprod()
    df["bh_equity"] = (1 + df["bh_ret"].fillna(0)).cumprod()

    df["strategy_dd"] = df["strategy_equity"] / df["strategy_equity"].cummax() - 1.0
    df["bh_dd"] = df["bh_equity"] / df["bh_equity"].cummax() - 1.0

    df["trade_flag"] = (df["exposure"].diff().abs() >= 1e-12).astype(int)
    df.loc[df["exposure"].isna() | df["exposure"].shift(1).isna(), "trade_flag"] = 0
    df["trade_count"] = df["trade_flag"].cumsum()

    return df


# ------------------------------------------------------------
# Helpers for complex agent overlay
# ------------------------------------------------------------
def _safe_clip01(s: pd.Series) -> pd.Series:
    return s.replace([np.inf, -np.inf], np.nan).clip(0.0, 1.0)


def _asymmetric_smoothing(values: np.ndarray, down_speed: float, up_speed: float, start: float = 1.0) -> np.ndarray:
    """
    Asymmetric smoothing:
      if v < prev: prev += down_speed*(v-prev)
      else:        prev += up_speed*(v-prev)
    """
    out = []
    prev = float(start)
    ds = float(down_speed)
    us = float(up_speed)
    for v in values:
        v = float(v)
        if v < prev:
            prev = prev + ds * (v - prev)
        else:
            prev = prev + us * (v - prev)
        out.append(prev)
    return np.array(out, dtype=float)


# ------------------------------------------------------------
# 2) Complex agent: DD + Tail + DownsideVol gate + smoothing
# ------------------------------------------------------------
def compute_complex_agent_overlay(
    df: pd.DataFrame,
    # --- Drawdown overlay ---
    dd_enter: float = -0.08,
    dd_full: float = -0.25,
    floor: float = 0.20,
    # --- Tail crash brake ---
    vol_fast_span: int = 20,
    sigma_k: float = 3.0,
    tail_cap: float = 0.40,
    # --- Downside vol brake ---
    window_dvol: int = 63,
    target_dvol: float = 0.20,
    alpha: float = 0.60,
    use_dvol_dd: float = -0.12,
    # --- Smoothing ---
    down_speed: float = 0.50,
    up_speed: float = 0.30,
    # --- Transaction cost ---
    transaction_cost: float = 0.001,  # 0.1% per 1.0 notional traded (turnover-based)
) -> pd.DataFrame:
    """
    Faithful port of your uploaded complex agent.py (core mechanics):
      overlay_dd: drawdown-based scaling
      overlay_tail: 2-day tail crash brake using fast EWM vol
      overlay_dvol_gate: downside vol brake only when drawdown < use_dvol_dd
      overlay_raw = overlay_dd * overlay_tail * overlay_dvol_gate
      overlay = asymmetric smoothing (down_speed/up_speed)
      exposure = overlay.shift(1)   (avoid look-ahead)
      strategy_ret = exposure * ret - turnover*transaction_cost

    Returns are computed with pct_change() to match complex agent behavior.

    Outputs include the columns your run_demo/report pipeline expects:
      ret, vol, exposure_target, exposure, strategy_ret, bh_ret,
      strategy_equity, bh_equity, strategy_dd, bh_dd, trade_flag, trade_count,
      plus diagnostic columns: overlay_dd, overlay_tail, overlay_dvol, overlay_raw, overlay, drawdown, turnover, tcost_ret.
    """
    df = df.copy()

    # 1) Simple returns (match complex agent.py)
    df["ret"] = df["Close"].pct_change()
    df["bh_ret"] = df["ret"]
    df["bh_equity"] = (1 + df["bh_ret"].fillna(0)).cumprod()

    # 2) Drawdown
    peak = df["Close"].cummax()
    df["drawdown"] = df["Close"] / peak - 1.0

    # 3) Drawdown overlay: linear map from dd_enter->1 down to dd_full->floor
    # x=0 at dd_enter; x=1 at dd_full (more negative). Clip 0..1
    x = ((df["drawdown"] - dd_enter) / (dd_full - dd_enter)).clip(0.0, 1.0)
    df["overlay_dd"] = (1.0 - x) * 1.0 + x * float(floor)
    df["overlay_dd"] = _safe_clip01(df["overlay_dd"]).fillna(1.0)

    # 4) Tail crash brake: ret < -K*sigma_fast, confirmed 2 consecutive days
    sigma_fast = df["ret"].ewm(span=int(vol_fast_span), adjust=False).std()
    df["sigma_fast"] = sigma_fast

    tail = df["ret"] < (-float(sigma_k) * sigma_fast)
    crash_tail = tail & tail.shift(1).fillna(False)
    df["crash_tail"] = crash_tail

    df["overlay_tail"] = np.where(df["crash_tail"], float(tail_cap), 1.0)
    df["overlay_tail"] = _safe_clip01(pd.Series(df["overlay_tail"], index=df.index)).fillna(1.0)

    # 5) Downside vol brake (gated by drawdown)
    neg = df["ret"].clip(upper=0.0)  # only downside moves
    downside_vol = neg.rolling(int(window_dvol)).std() * np.sqrt(ANN)
    df["downside_vol"] = downside_vol

    # Raw downside overlay: (target_dvol / downside_vol)^alpha, clipped 0..1
    overlay_dvol_raw = (float(target_dvol) / df["downside_vol"]) ** float(alpha)
    overlay_dvol_raw = overlay_dvol_raw.replace([np.inf, -np.inf], np.nan).fillna(1.0)
    df["overlay_dvol"] = _safe_clip01(overlay_dvol_raw)

    # Gate: only apply downside overlay if drawdown is sufficiently negative
    df["overlay_dvol_gate"] = np.where(df["drawdown"] < float(use_dvol_dd), df["overlay_dvol"], 1.0)
    df["overlay_dvol_gate"] = _safe_clip01(pd.Series(df["overlay_dvol_gate"], index=df.index)).fillna(1.0)

    # 6) Composite overlay raw
    df["overlay_raw"] = _safe_clip01(df["overlay_dd"] * df["overlay_tail"] * df["overlay_dvol_gate"]).fillna(1.0)

    # 7) Asymmetric smoothing
    smoothed = _asymmetric_smoothing(
        df["overlay_raw"].fillna(1.0).values,
        down_speed=float(down_speed),
        up_speed=float(up_speed),
        start=1.0,
    )
    df["overlay"] = _safe_clip01(pd.Series(smoothed, index=df.index)).fillna(1.0)

    # Suggested exposure for reporting consistency
    df["exposure_target"] = df["overlay"].clip(0.0, 1.0)

    # Executed exposure (shift 1 day to avoid look-ahead)
    df["exposure"] = df["overlay"].shift(1).clip(0.0, 1.0)

    # 8) Transaction cost via turnover (continuous exposure -> turnover makes sense)
    df["turnover"] = df["exposure"].diff().abs().fillna(0.0)
    df["tcost_ret"] = df["turnover"] * float(transaction_cost)

    # 9) Strategy return net of cost
    df["strategy_ret"] = df["exposure"] * df["ret"] - df["tcost_ret"]

    df["strategy_equity"] = (1 + df["strategy_ret"].fillna(0)).cumprod()

    df["strategy_dd"] = df["strategy_equity"] / df["strategy_equity"].cummax() - 1.0
    df["bh_dd"] = df["bh_equity"] / df["bh_equity"].cummax() - 1.0

    # 10) Trade stats (for reporting; in continuous exposure this counts any change)
    df["trade_flag"] = (df["exposure"].diff().abs() > 1e-12).astype(int)
    df.loc[df["exposure"].isna() | df["exposure"].shift(1).isna(), "trade_flag"] = 0
    df["trade_count"] = df["trade_flag"].cumsum()

    # 11) For chart compatibility: rolling annualized vol proxy
    df["vol"] = df["ret"].rolling(20).std() * np.sqrt(ANN)

    return df
