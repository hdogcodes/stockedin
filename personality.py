"""Simple, deterministic "portfolio personality" tags computed from holdings.

No sector/fundamentals API calls — just a small curated ticker list and
concentration math, kept intentionally simple per the brief.
"""

TECH_TICKERS = {
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "NVDA", "TSLA", "AMD",
    "CRM", "ORCL", "ADBE", "NFLX", "INTC", "CSCO", "AVGO", "QCOM", "IBM",
}

GROWTH_TICKERS = {
    "TSLA", "NVDA", "AMZN", "META", "SHOP", "SQ", "ROKU", "PLTR", "COIN",
    "AMD", "NET", "SNOW", "CRWD",
}


def compute_personality(portfolio):
    """Return up to 3 short personality labels, or [] for an empty portfolio."""
    holdings = portfolio.holdings
    n = len(holdings)
    if n == 0:
        return []

    tickers = [h.ticker.upper() for h in holdings]
    tags = []

    if n <= 3:
        tags.append("🎯 Concentrated")

    tech_share = sum(1 for t in tickers if t in TECH_TICKERS) / n
    if tech_share >= 0.5:
        tags.append("💻 Tech Heavy")

    us_share = sum(1 for t in tickers if "." not in t) / n
    if us_share == 1:
        tags.append("🇺🇸 US Focused")

    growth_share = sum(1 for t in tickers if t in GROWTH_TICKERS) / n
    if growth_share >= 0.4:
        tags.append("🚀 Aggressive Growth")

    return tags[:3]
