# File: src/analytics.py

import pandas as pd
import numpy as np


def run_relative_valuation(df_market, target_ticker):
    """
    Performs Relative Valuation (Comparable Company Analysis).
    Calculates P/E, P/S, and EV/EBITDA multiples and compares the target
    against the peer group average.
    """
    df_calc = df_market.copy()

    # Calculate Multiples
    df_calc['P/E'] = df_calc['Price'] / df_calc['EPS']
    df_calc['P/S'] = df_calc['Market Cap'] / df_calc['Revenue']
    df_calc['EV/EBITDA'] = df_calc['Enterprise Value'] / df_calc['EBITDA']

    df_calc = df_calc.round(2)

    # Separate Target and Peers
    target_data = df_calc[df_calc['Ticker'] == target_ticker].iloc[0]
    peer_data = df_calc[df_calc['Ticker'] != target_ticker]

    # Calculate Peer Averages
    peer_means = peer_data[['P/E', 'P/S', 'EV/EBITDA']].mean()

    valuation_summary = {}
    for metric in ['P/E', 'P/S', 'EV/EBITDA']:
        target_val = target_data[metric]
        peer_val = peer_means[metric]

        # Handle missing data
        if pd.isna(target_val) or pd.isna(peer_val):
            valuation_summary[metric] = "Data Unavailable"
            continue

        # Calculate premium/discount percentage
        diff = ((target_val - peer_val) / peer_val) * 100
        status = "Premium" if diff > 0 else "Discount"

        valuation_summary[metric] = {
            "Target": target_val,
            "Peer_Avg": round(peer_val, 2),
            "Status": status,
            "Difference": round(diff, 2)
        }

    return valuation_summary, df_calc