"""Default research universe, fixed BEFORE any backtest was run.

Large, heavily traded US stocks and ETFs across sectors plus commonly traded high-beta names.
Caveat: this is today's list, so delisted or collapsed names are missing (survivorship bias).
Point-in-time universes need a vendor with delisted symbols (e.g. Polygon/Massive flat files).
"""

DEFAULT_UNIVERSE = [
    # mega/large-cap tech and communication
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "AMD", "NFLX", "ORCL", "CRM", "ADBE",
    "INTC", "MU", "QCOM", "ARM", "SMCI", "PLTR", "SNOW", "PANW", "CRWD", "NET", "DDOG", "SHOP", "UBER",
    "ABNB", "COIN", "HOOD", "MSTR", "RBLX", "SOFI",
    # financials, energy, industrials, consumer, health
    "JPM", "BAC", "GS", "WFC", "XOM", "CVX", "OXY", "BA", "CAT", "GE", "NKE", "DIS", "WMT", "COST", "TGT",
    "SBUX", "F", "GM", "RIVN", "LLY", "UNH", "PFE", "MRNA",
    # ETFs
    "SPY", "QQQ", "IWM", "SMH", "XLE", "XLF", "TLT", "GLD",
]
