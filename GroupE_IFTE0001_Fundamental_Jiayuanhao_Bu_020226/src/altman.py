import pandas as pd
import yfinance as yf

FINANCIAL_FIELD_MAP = {
    "Revenue": {"source": "income", "fields": ["Total Revenue"]},
    "Net_Income": {"source": "income", "fields": ["Net Income"]},
    "Total_Assets": {"source": "balance", "fields": ["Total Assets"]},
    "Total_Debt": {"source": "balance", "fields": ["Total Debt"]},
    "Equity": {
        "source": "balance",
        "fields": [
            "Total Stockholder Equity",
            "Stockholders Equity",
            "Total Equity Gross Minority Interest",
            "Total Equity",
        ],
    },
}

ALT_MAN_WEIGHTS = {"X1": 1.2, "X2": 1.4, "X3": 3.3, "X4": 0.6, "X5": 1.0}
Z_SCORE_THRESHOLDS = {"SAFE": 2.99, "GREY": 1.81}

def build_financial_dataframe(ticker="AMZN", field_map=FINANCIAL_FIELD_MAP):
    stock = yf.Ticker(ticker)
    income_stmt = stock.financials.T
    balance_sheet = stock.balance_sheet.T

    def get_first_available(df, possible_fields):
        for field in possible_fields:
            if field in df.columns:
                return df[field]
        raise KeyError(f"None of these fields found: {possible_fields}")

    data = {}
    for output_field, config in field_map.items():
        source = config["source"]
        possible_fields = config["fields"]
        df_source = income_stmt if source == "income" else balance_sheet
        data[output_field] = get_first_available(df_source, possible_fields)

    df = pd.DataFrame(data)
    df = df.sort_index().tail(5)
    df.index = df.index.year.astype(str)
    return df

def compute_altman_z_score(df: pd.DataFrame, weights=ALT_MAN_WEIGHTS) -> pd.Series:
    X1 = 0  # conservative assumption
    X2 = df["Equity"] / df["Total_Assets"]
    X3 = df["Net_Income"] / df["Total_Assets"]
    X4 = df["Equity"] / df["Total_Debt"]
    X5 = df["Revenue"] / df["Total_Assets"]

    z_score = (
        weights["X1"] * X1
        + weights["X2"] * X2
        + weights["X3"] * X3
        + weights["X4"] * X4
        + weights["X5"] * X5
    )
    return z_score

def classify_z_score(z: float, thresholds=Z_SCORE_THRESHOLDS) -> str:
    if z > thresholds["SAFE"]:
        return "Safe Zone"
    elif z >= thresholds["GREY"]:
        return "Grey Zone"
    return "Distress Zone"
