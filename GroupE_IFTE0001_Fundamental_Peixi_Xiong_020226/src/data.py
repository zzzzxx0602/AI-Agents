from __future__ import annotations
import pandas as pd
import yfinance as yf

def pick_col(df: pd.DataFrame, candidates) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None

def filter_fiscal_years(df: pd.DataFrame, fiscal_years: tuple[int, ...]) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, errors="coerce")
    df = df[df.index.notna()]
    return df[df.index.year.isin(list(fiscal_years))].sort_index()

def fetch_market_info(symbol: str) -> tuple[yf.Ticker, dict]:
    t = yf.Ticker(symbol)
    info = {}
    try:
        info = t.info or {}
    except Exception:
        info = {}
    # Robust price fallback
    if info.get("currentPrice") is None:
        try:
            info["currentPrice"] = float(t.history(period="5d")["Close"].dropna().iloc[-1])
        except Exception:
            info["currentPrice"] = None
    return t, info

def fetch_risk_free_rate(proxy: str = "^TNX") -> float:
    try:
        tnx = yf.Ticker(proxy)
        return float(tnx.history(period="5d")["Close"].dropna().iloc[-1]) / 100.0
    except Exception:
        return 0.04

def fetch_statements(t: yf.Ticker) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    income = t.financials.T if t.financials is not None else pd.DataFrame()
    balance = t.balance_sheet.T if t.balance_sheet is not None else pd.DataFrame()
    cashflow = t.cashflow.T if t.cashflow is not None else pd.DataFrame()
    return income, balance, cashflow

def fetch_price_history(symbol: str, years: int = 10) -> pd.DataFrame:
    period = f"{max(1, years)}y"
    return yf.download(symbol, period=period, auto_adjust=True, progress=False)
