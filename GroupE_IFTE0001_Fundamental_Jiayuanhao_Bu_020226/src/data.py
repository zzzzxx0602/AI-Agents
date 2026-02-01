import yfinance as yf

def get_stock(ticker: str):
    return yf.Ticker(ticker)

def fetch_statements(ticker: str):
    """Return (stock, annual_income, annual_balance, quarterly_income)."""
    stock = get_stock(ticker)
    income_raw = stock.financials
    balance_raw = stock.balance_sheet
    quarterly_raw = stock.quarterly_financials
    return stock, income_raw, balance_raw, quarterly_raw
