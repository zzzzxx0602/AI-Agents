from dataclasses import dataclass

@dataclass
class Config:
    # Fiscal-year filter requested in the coursework brief (5 years minimum).
    # We target 2019–2024 (6 years) when available from Yahoo Finance.
    fiscal_years: tuple[int, ...] = (2019, 2020, 2021, 2022, 2023, 2024)

    # Market / valuation assumptions
    risk_free_proxy: str = "^TNX"          # 10Y Treasury yield proxy on Yahoo Finance
    equity_risk_premium: float = 0.055     # documented ERP assumption (5.5%)
    rd_spread_fallback: float = 0.015      # fallback debt spread if interest expense is missing
    tax_rate_fallback: float = 0.21        # fallback effective tax rate

    # DCF assumptions (simple but defensible)
    projection_years: int = 5
    terminal_growth: float = 0.025

    # Sensitivity grid deltas (around base case)
    wacc_deltas: tuple[float, ...] = (-0.02, -0.01, 0.00, 0.01, 0.02)
    g_deltas: tuple[float, ...] = (-0.01, -0.005, 0.00, 0.005, 0.01)

    # LLM configuration (choose one)
    # - provider="openai": requires OPENAI_API_KEY in environment
    # - provider="ollama": requires local Ollama server (default http://localhost:11434)
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # Output directories
    out_data: str = "data"
    out_tables: str = "tables"
    out_charts: str = "charts"
    out_reports: str = "reports"
