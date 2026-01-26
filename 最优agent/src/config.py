from dataclasses import dataclass

@dataclass
class AgentConfig:
    ticker: str = "AMZN"
    start: str = "2015-01-01"
    end: str | None = None

    # --- Indicators ---
    atr_period: int = 10
    supertrend_multiplier: float = 3.0

    chandelier_lookback: int = 22
    chandelier_k: float = 3.0

    # --- Strategy Logic ---
    enable_reentry: bool = True

    # --- Risk Management ---
    initial_equity: float = 100_000.0
    risk_pct_equity: float = 0.01          # Risk 1% of equity per trade
    hard_stop_atr_multiple: float = 2.0
    use_trailing_stop: bool = True

    # --- Volatility Targeting (Dynamic Sizing) ---
    target_ann_vol: float = 0.10      # Target 10% annualized volatility (Conservative)
    strategy_vol_lookback: int = 60   # Lookback window for realized vol calculation
    max_leverage: float = 1.5         # Cap leverage at 1.5x to prevent excessive risk
    min_leverage: float = 1.0         # Minimum leverage floor

    # --- Execution Simulation ---
    commission_bps: float = 5.0       # 5 basis points per trade
    slippage_bps: float = 1.0         # 1 basis point slippage

    # --- Backtest Controls ---
    allow_reentry_same_day: bool = False
    min_atr: float = 1e-6