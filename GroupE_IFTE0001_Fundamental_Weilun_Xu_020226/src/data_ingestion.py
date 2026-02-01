# File: src/data_ingestion.py

import yfinance as yf
import pandas as pd
from openai import OpenAI
from src.config import API_KEY, MODEL_NAME

# Initialize OpenAI Client (Safe handling if key is missing)
if API_KEY:
    client = OpenAI(api_key=API_KEY)
else:
    client = None


def get_ticker_from_name(user_input):
    """
    Translates a company name (e.g., 'Starbucks') into a stock ticker (e.g., 'SBUX').
    """
    if not client:
        print("Error: API Key is missing in src/config.py")
        return "ERROR"

    try:
        prompt = f"What is the stock ticker symbol for '{user_input}' on the US stock market? Return ONLY the ticker symbol (e.g., AAPL). If it is not a public company or you are unsure, return 'NOT_FOUND'. Do not write any other text."

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a financial assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        ticker = response.choices[0].message.content.strip().upper()
        # Clean potential formatting artifacts
        ticker = ticker.replace(".", "").replace(" ", "")
        return ticker
    except Exception as e:
        print(f"Error identifying ticker: {e}")
        return "NOT_FOUND"


def get_peers_automatically(target_ticker):
    """
    Dynamically identifies a peer group for relative valuation using LLM reasoning.
    """
    if not client:
        return []

    try:
        prompt = f"Identify 3 major public competitor companies for {target_ticker}. Return ONLY their stock ticker symbols separated by a comma (e.g., 'AAPL, MSFT, GOOGL'). Do not write any other text."

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a financial data assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        content = response.choices[0].message.content.strip()
        peers = [x.strip().upper() for x in content.split(',')]

        # Ensure target is not in the peer list
        if target_ticker in peers:
            peers.remove(target_ticker)

        return peers[:3]
    except Exception as e:
        print(f"Error auto-detecting peers: {e}")
        return []


def get_current_market_data(ticker_list):
    """
    Ingests real-time market data via yfinance (Price, Market Cap, EV, EBITDA, etc.).
    """
    data_list = []
    for ticker in ticker_list:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            company_data = {
                "Ticker": ticker,
                "Price": info.get('currentPrice'),
                "Market Cap": info.get('marketCap'),
                "Enterprise Value": info.get('enterpriseValue'),
                "EBITDA": info.get('ebitda'),
                "Revenue": info.get('totalRevenue'),
                "EPS": info.get('trailingEps')
            }
            data_list.append(company_data)
        except Exception:
            pass  # Skip invalid tickers gracefully
    return pd.DataFrame(data_list)


def get_historical_fundamentals(ticker):
    """
    Ingests 5 years of historical financial statements to compute quality ratios.
    """
    try:
        stock = yf.Ticker(ticker)
        financials = stock.financials.T
        balance_sheet = stock.balance_sheet.T

        # Analyze last 5 years
        years_to_analyze = 5
        financials = financials.head(years_to_analyze)
        balance_sheet = balance_sheet.head(years_to_analyze)

        df_hist = pd.DataFrame()

        # Extract raw line items
        df_hist['Net Income'] = financials['Net Income']
        df_hist['Total Revenue'] = financials['Total Revenue']
        df_hist['Total Assets'] = balance_sheet['Total Assets']
        df_hist['Total Equity'] = balance_sheet['Stockholders Equity']

        # Handle debt field variations
        if 'Total Debt' in balance_sheet.columns:
            df_hist['Total Debt'] = balance_sheet['Total Debt']
        else:
            df_hist['Total Debt'] = balance_sheet.get('Total Liabilities Net Minority Interest', 0)

        # Compute Ratios
        df_hist['ROE (%)'] = (df_hist['Net Income'] / df_hist['Total Equity']) * 100
        df_hist['Debt/Equity'] = df_hist['Total Debt'] / df_hist['Total Equity']
        # Use default method for pct_change to ensure compatibility
        df_hist['Revenue Growth (%)'] = df_hist['Total Revenue'].pct_change(periods=-1) * 100
        df_hist['Asset Turnover'] = df_hist['Total Revenue'] / df_hist['Total Assets']

        return df_hist[['ROE (%)', 'Debt/Equity', 'Revenue Growth (%)', 'Asset Turnover']].round(2)

    except Exception as e:
        print(f"Error fetching history: {e}")
        return pd.DataFrame()