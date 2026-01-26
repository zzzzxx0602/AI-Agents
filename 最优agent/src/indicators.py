import pandas as pd

def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 10) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([
        (high - low),
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, adjust=False).mean()

def supertrend(df: pd.DataFrame, atr_period: int = 10, multiplier: float = 3.0) -> pd.DataFrame:
    high, low, close = df["High"], df["Low"], df["Close"]
    hl2 = (high + low) / 2.0
    atr_val = atr(high, low, close, atr_period)

    upperband = hl2 + (multiplier * atr_val)
    lowerband = hl2 - (multiplier * atr_val)

    final_upper = upperband.copy()
    final_lower = lowerband.copy()

    for i in range(1, len(df)):
        if (upperband.iloc[i] < final_upper.iloc[i-1]) or (close.iloc[i-1] > final_upper.iloc[i-1]):
            final_upper.iloc[i] = upperband.iloc[i]
        else:
            final_upper.iloc[i] = final_upper.iloc[i-1]

        if (lowerband.iloc[i] > final_lower.iloc[i-1]) or (close.iloc[i-1] < final_lower.iloc[i-1]):
            final_lower.iloc[i] = lowerband.iloc[i]
        else:
            final_lower.iloc[i] = final_lower.iloc[i-1]

    st = pd.Series(index=df.index, dtype=float)
    direction = pd.Series(index=df.index, dtype=int)

    st.iloc[0] = final_upper.iloc[0]
    direction.iloc[0] = -1

    for i in range(1, len(df)):
        prev_dir = direction.iloc[i-1]
        c = close.iloc[i]

        if prev_dir == -1:
            if c > final_upper.iloc[i]:
                direction.iloc[i] = 1
                st.iloc[i] = final_lower.iloc[i]
            else:
                direction.iloc[i] = -1
                st.iloc[i] = final_upper.iloc[i]
        else:
            if c < final_lower.iloc[i]:
                direction.iloc[i] = -1
                st.iloc[i] = final_upper.iloc[i]
            else:
                direction.iloc[i] = 1
                st.iloc[i] = final_lower.iloc[i]

    return pd.DataFrame({
        "supertrend": st,
        "st_dir": direction,
        "atr": atr_val,
    }, index=df.index)

def chandelier_exit_long(df: pd.DataFrame, atr_series: pd.Series, lookback: int = 22, k: float = 3.0) -> pd.Series:
    hh = df["High"].rolling(window=lookback, min_periods=lookback).max()
    raw = hh - k * atr_series
    stop = raw.copy()
    for i in range(1, len(stop)):
        if pd.isna(stop.iloc[i-1]) or pd.isna(stop.iloc[i]):
            continue
        stop.iloc[i] = max(stop.iloc[i-1], stop.iloc[i])
    return stop