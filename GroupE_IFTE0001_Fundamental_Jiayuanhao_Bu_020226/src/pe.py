import yfinance as yf
import numpy as np

def get_pe_ttm_from_yahoo(ticker: str):
    stock = yf.Ticker(ticker)
    price_data = stock.history(period="1d")
    if price_data.empty:
        return None
    price = float(price_data["Close"].iloc[-1])
    eps_ttm = stock.info.get("trailingEps")
    if eps_ttm is None or eps_ttm <= 0:
        return None
    return round(price / eps_ttm, 2)

def get_peer_tickers(ticker: str, max_peers=10):
    stock = yf.Ticker(ticker)
    sector = stock.info.get("sector")
    default_peers = {
        "Technology": ["AAPL", "MSFT", "GOOGL", "META", "NVDA"],
        "Consumer Cyclical": ["TGT", "BABA", "JD", "WMT", "COST"],
        "Financial Services": ["JPM", "BAC", "GS", "MS"],
        "Healthcare": ["JNJ", "PFE", "MRK", "UNH"],
    }
    return default_peers.get(sector, ["AAPL", "MSFT", "GOOGL", "META"])[:max_peers]

def compute_dynamic_pe_redline(ticker: str, safety_multiple=1.5):
    peers = get_peer_tickers(ticker)
    peer_pes = []
    for peer in peers:
        pe = get_pe_ttm_from_yahoo(peer)
        if pe is not None:
            peer_pes.append(pe)
    if len(peer_pes) == 0:
        return None
    median_pe = float(np.median(peer_pes))
    dynamic_redline = round(median_pe * safety_multiple, 2)
    return dynamic_redline, round(median_pe, 2), peer_pes

def pe_valuation_check(pe: float, dynamic_redline: float):
    if pe <= dynamic_redline:
        valuation_result = "Pass"
        assessment_text = (
            f"The company's Trailing P/E ratio of {pe} remains below the "
            f"market-derived red-line threshold of {dynamic_redline}, computed from peer multiples. "
            f"Under this dynamic screening framework, the valuation does not indicate extreme overvaluation risk."
        )
    else:
        valuation_result = "Fail"
        assessment_text = (
            f"The company's Trailing P/E ratio of {pe} exceeds the "
            f"market-derived red-line threshold of {dynamic_redline}, computed from peer multiples. "
            f"This suggests elevated valuation risk under the dynamic screening framework."
        )
    return valuation_result, assessment_text
