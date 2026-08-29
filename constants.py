"""Shared choice lists for portfolio tags/goals/risk and prediction directions.

Centralized so forms, templates, and explore filtering all reference the
same canonical strings instead of drifting.
"""

PORTFOLIO_TAGS = [
    "🚀 Growth",
    "💰 Dividend",
    "🤖 AI",
    "💻 Technology",
    "🌱 Sustainable",
    "🛡️ Low Risk",
    "🌎 Global",
    "🎓 Student",
]

PORTFOLIO_GOALS = [
    "🏠 First Home",
    "🎓 Education",
    "💰 Long-Term Wealth",
    "💵 Passive Income",
    "🚀 High Growth",
    "🛡️ Preserve Capital",
]

RISK_LEVELS = ["Low", "Medium", "High"]

PREDICTION_DIRECTIONS = ["outperform", "underperform"]

DEFAULT_BENCHMARK = "SPY"
