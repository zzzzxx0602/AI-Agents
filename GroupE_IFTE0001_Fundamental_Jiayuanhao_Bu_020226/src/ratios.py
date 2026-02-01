import pandas as pd
import matplotlib.pyplot as plt

def compute_ratios(income_df: pd.DataFrame, balance_df: pd.DataFrame):
    gross_margin_df = pd.DataFrame({
        "Gross Margin": (income_df["Total Revenue"] - income_df["Cost of Revenue"]) / income_df["Total Revenue"]
    })

    roe_df = pd.DataFrame({
        "ROE": income_df["Net Income"] / balance_df["Shareholders' Equity"]
    })

    de_ratio_df = pd.DataFrame({
        "Debt-to-Equity": balance_df["Total Debt"] / balance_df["Shareholders' Equity"]
    })

    asset_turnover_df = pd.DataFrame({
        "Asset Turnover": income_df["Total Revenue"] / balance_df["Total Assets"]
    })

    return gross_margin_df, roe_df, de_ratio_df, asset_turnover_df

def plot_ratio(df: pd.DataFrame, title: str, ylabel: str, save_path: str | None = None):
    plt.figure()
    plt.plot(df.index, df.iloc[:, 0], marker="o")
    plt.title(title)
    plt.xlabel("Year")
    plt.ylabel(ylabel)
    plt.grid(True)
    if save_path:
        plt.savefig(save_path, bbox_inches="tight", dpi=180)
    else:
        plt.show()
    plt.close()
