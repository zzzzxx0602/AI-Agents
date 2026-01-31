# run_demo.py
from __future__ import annotations

import os
from datetime import date
import pandas as pd
import matplotlib.pyplot as plt

from src.data import load_price_data
from src.strategy import compute_complex_agent_overlay
from src.metrics import cagr, sharpe_ratio, max_drawdown, total_return, hit_rate_on_rebalances

from src.report import (
    vol_overlay_signal_and_action,
    build_vol_overlay_llm_prompt,
    try_generate_llm_commentary,
    build_trade_note_markdown_vol_overlay,
    build_trade_note_html_vol_overlay,
)

ANN = 252

# --------------------------
# Params 
# --------------------------
PARAMS = {
    "ticker": "AMZN",
    "start": "2014-01-01",
    "end": None,

    # Drawdown overlay
    "dd_enter": -0.08,
    "dd_full": -0.25,
    "floor": 0.20,

    # Tail crash brake
    "vol_fast_span": 20,
    "sigma_k": 3.0,
    "tail_cap": 0.40,

    # Downside vol brake
    "window_dvol": 63,
    "target_dvol": 0.20,
    "alpha": 0.60,
    "use_dvol_dd": -0.12,

    # Smoothing
    "down_speed": 0.50,
    "up_speed": 0.30,

    # Costs + Sharpe
    "transaction_cost": 0.001,  # 0.1% per 1.0 notional traded
    "rf_annual": 0.04,          # 4% annual risk-free rate for Sharpe

    # For report function compatibility (used in signal/action + prompt wording)
    # This is NOT driving the strategy here; it's only for regime labeling in the report.
    "target_vol": 0.20,
    "rebalance_threshold": 0.05,
}


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


# --------------------------
# Charts (4 key figures)
# --------------------------
def save_equity_chart(df: pd.DataFrame, out_path: str, ticker: str) -> None:
    plt.figure(figsize=(10, 4))
    plt.plot(df.index, df["bh_equity"], label="Buy & Hold")
    plt.plot(df.index, df["strategy_equity"], label="Strategy (net costs)")
    plt.title(f"{ticker}: Equity Curve (Normalized)")
    plt.xlabel("Date")
    plt.ylabel("Equity")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def save_rolling_vol_chart(df: pd.DataFrame, target_vol: float, out_path: str, ticker: str) -> None:
    plt.figure(figsize=(10, 4))
    # Use df["vol"] if present (we set it in strategy for compatibility)
    plt.plot(df.index, df["vol"], label="Rolling Vol (ann.)")
    plt.axhline(y=float(target_vol), linestyle="--", label="Reference Target Vol")
    plt.title(f"{ticker}: Rolling Volatility (Annualized)")
    plt.xlabel("Date")
    plt.ylabel("Vol")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def save_exposure_chart(df: pd.DataFrame, out_path: str, ticker: str) -> None:
    plt.figure(figsize=(10, 4))
    plt.plot(df.index, df["exposure"], label="Executed Exposure (t-1)")
    plt.title(f"{ticker}: Exposure (Complex Overlay)")
    plt.xlabel("Date")
    plt.ylabel("Exposure")
    plt.ylim(0, 1.05)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def save_drawdown_comparison(df: pd.DataFrame, out_path: str, ticker: str) -> None:
    plt.figure(figsize=(10, 4))
    plt.plot(df.index, df["bh_dd"], label="Buy & Hold DD", alpha=0.85)
    plt.plot(df.index, df["strategy_dd"], label="Strategy DD", alpha=0.95)
    plt.title(f"{ticker}: Drawdown Comparison")
    plt.xlabel("Date")
    plt.ylabel("Drawdown")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def main() -> None:
    ticker = PARAMS["ticker"]
    as_of_today = str(date.today())
    rf_annual = float(PARAMS.get("rf_annual", 0.0))

    print(f"--- Starting Technical Volatility Overlay Agent for {ticker} ---")
    print("Running backtest...")

    # 1) Load data
    df_px = load_price_data(ticker, start=PARAMS["start"], end=PARAMS["end"])

    # 2) Run complex agent overlay (aligned to complex agent.py)
    df = compute_complex_agent_overlay(
        df_px,
        dd_enter=PARAMS["dd_enter"],
        dd_full=PARAMS["dd_full"],
        floor=PARAMS["floor"],
        vol_fast_span=PARAMS["vol_fast_span"],
        sigma_k=PARAMS["sigma_k"],
        tail_cap=PARAMS["tail_cap"],
        window_dvol=PARAMS["window_dvol"],
        target_dvol=PARAMS["target_dvol"],
        alpha=PARAMS["alpha"],
        use_dvol_dd=PARAMS["use_dvol_dd"],
        down_speed=PARAMS["down_speed"],
        up_speed=PARAMS["up_speed"],
        transaction_cost=PARAMS["transaction_cost"],
    )

    # 3) Metrics (Rf-adjusted Sharpe)
    metrics = {
        "TotalReturn_buy_hold": float(total_return(df["bh_equity"])),
        "TotalReturn_strategy": float(total_return(df["strategy_equity"])),
        "CAGR_buy_hold": float(cagr(df["bh_equity"])),
        "CAGR_strategy": float(cagr(df["strategy_equity"])),
        "Sharpe_buy_hold": float(sharpe_ratio(df["bh_ret"], rf_annual=rf_annual)),
        "Sharpe_strategy": float(sharpe_ratio(df["strategy_ret"], rf_annual=rf_annual)),
        "MaxDD_buy_hold": float(max_drawdown(df["bh_equity"])),
        "MaxDD_strategy": float(max_drawdown(df["strategy_equity"])),
        "HitRate_strategy": float(hit_rate_on_rebalances(df)),
        "Rebalance_trades": int(df["trade_flag"].sum()),
    }

    # Optional extra stats (nice to have for debugging / report)
    total_turnover = float(df["turnover"].fillna(0.0).sum()) if "turnover" in df.columns else float("nan")
    total_tcost = float(df["tcost_ret"].fillna(0.0).sum()) if "tcost_ret" in df.columns else float("nan")

    # 4) Latest state (for signal/action + report prompt)
    latest = df[df["exposure"].notna()].iloc[-1]
    latest_state = {
        "date": str(latest.name.date()),
        "latest_close": float(latest["Close"]),
        "realized_vol_annualized": float(latest.get("vol", float("nan"))),
        "suggested_exposure": float(latest.get("exposure_target", latest.get("overlay", float("nan")))),
        "executed_exposure": float(latest["exposure"]),
    }

    # 5) Save charts
    reports_dir = "reports"
    ensure_dir(reports_dir)

    equity_path = os.path.join(reports_dir, "equity_curve.png")
    vol_path = os.path.join(reports_dir, "rolling_vol.png")
    exposure_path = os.path.join(reports_dir, "exposure.png")
    drawdown_path = os.path.join(reports_dir, "drawdown_comparison.png")

    save_equity_chart(df, equity_path, ticker)
    save_rolling_vol_chart(df, PARAMS["target_vol"], vol_path, ticker)
    save_exposure_chart(df, exposure_path, ticker)
    save_drawdown_comparison(df, drawdown_path, ticker)

    print("Charts saved:")
    print(f"- {equity_path}")
    print(f"- {vol_path}")
    print(f"- {exposure_path}")
    print(f"- {drawdown_path}")

    charts = {
        "equity": equity_path,
        "vol": vol_path,
        "exposure": exposure_path,
        "drawdown": drawdown_path,
    }

    # 6) Signal/Action (keeps your existing report style)
    # Note: This is based on vol regime labeling; complex agent uses other brakes too.
    signal_text, action_text = vol_overlay_signal_and_action(
        latest_state={
            "realized_vol_annualized": latest_state["realized_vol_annualized"],
            "suggested_exposure": latest_state["suggested_exposure"],
            "executed_exposure": latest_state["executed_exposure"],
        },
        params={
            "target_vol": PARAMS["target_vol"],
            "rebalance_threshold": PARAMS["rebalance_threshold"],
        },
    )

    # 7) AI Commentary
    print("\nGenerating AI Commentary...")
    prompt = build_vol_overlay_llm_prompt(
        ticker=ticker,
        as_of=latest_state["date"],
        params=PARAMS,
        metrics=metrics,
        latest_state={
            "realized_vol_annualized": latest_state["realized_vol_annualized"],
            "suggested_exposure": latest_state["suggested_exposure"],
            "executed_exposure": latest_state["executed_exposure"],
        },
    )
    llm_text = try_generate_llm_commentary(prompt)

    # Append a tiny factual line to help the AI/report be consistent about costs (optional)
    if llm_text:
        llm_text = (
            llm_text.strip()
            + f"\n- Transaction cost: 0.10% per 1.0 notional traded (turnover-based)."
            + f"\n- Total turnover (sum |Δexposure|): {total_turnover:.2f}; approx total cost drag (sum): {total_tcost:.4f}."
        )

    # 8) Build reports (md + html)
    md_text = build_trade_note_markdown_vol_overlay(
        ticker=ticker,
        params=PARAMS,
        metrics=metrics,
        signal_text=signal_text,
        action_text=action_text,
        as_of=latest_state["date"],
        llm_text=llm_text,
    )

    html_text = build_trade_note_html_vol_overlay(
        ticker=ticker,
        params=PARAMS,
        metrics=metrics,
        signal_text=signal_text,
        action_text=action_text,
        as_of=latest_state["date"],
        charts=charts,
        llm_text=llm_text,
    )

    md_path = os.path.join(reports_dir, "trade_note.md")
    html_path = os.path.join(reports_dir, "trade_note.html")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_text)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_text)

    # 9) Console output
    print("\n==============================")
    print("FINAL STRATEGY METRICS")
    print("==============================")
    for k in [
        "TotalReturn_strategy",
        "CAGR_strategy",
        "CAGR_buy_hold",
        "Sharpe_strategy",
        "MaxDD_strategy",
        "HitRate_strategy",
        "Rebalance_trades",
    ]:
        print(f"{k:<22}: {metrics[k]}")

    print(f"{'Total_turnover':<22}: {total_turnover}")
    print(f"{'Total_tcost_drag':<22}: {total_tcost}")

    print("\n=== Demo Complete ===")
    print(f"Markdown Report: {md_path}")
    print(f"HTML Report:     {html_path}")
    print(f"As-of (today):   {as_of_today}")
    print(f"Sharpe RF (ann): {rf_annual}")


if __name__ == "__main__":
    main()
