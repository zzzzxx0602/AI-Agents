from __future__ import annotations
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def plot_price(price_df: pd.DataFrame, path: str, title: str):
    if price_df is None or price_df.empty or "Close" not in price_df.columns:
        return
    plt.figure()
    price_df["Close"].dropna().plot()
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()

def plot_sensitivity_heatmap(sens_df: pd.DataFrame, path: str, title: str):
    vals = sens_df.values.astype(float)
    fig = plt.figure(figsize=(10, 6))
    ax = plt.gca()
    im = ax.imshow(vals, aspect="auto")
    ax.set_xticks(range(len(sens_df.columns)))
    ax.set_xticklabels(list(sens_df.columns))
    ax.set_yticks(range(len(sens_df.index)))
    ax.set_yticklabels(list(sens_df.index))
    ax.set_xlabel("WACC")
    ax.set_ylabel("Terminal Growth (g)")
    ax.set_title(title)

    for i in range(vals.shape[0]):
        for j in range(vals.shape[1]):
            v = vals[i, j]
            txt = "N/A" if np.isnan(v) else f"{v:.0f}"
            ax.text(j, i, txt, ha="center", va="center", fontsize=9)

    plt.colorbar(im, ax=ax, label="Fair Value per Share")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
