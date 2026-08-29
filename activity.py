"""Merges each portfolio's PortfolioUpdate entries and its owner's
predictions into a single recent-activity list for feed/profile cards.

Attaches a plain `.recent_activity` list attribute to each portfolio (not a
model property — it depends on render-time data, same pattern as `.stats`
from prices.attach_stats).
"""


def attach_activity(portfolios, limit=4):
    for p in portfolios:
        items = [
            {
                "kind": u.kind,
                "ticker": u.ticker,
                "body": u.body,
                "status": None,
                "created_at": u.created_at,
            }
            for u in p.updates
        ]
        items += [
            {
                "kind": "prediction",
                "ticker": pred.ticker,
                "body": pred.statement,
                "status": pred.status,
                "created_at": pred.created_at,
            }
            for pred in p.owner.predictions
        ]
        items.sort(key=lambda i: i["created_at"], reverse=True)
        p.recent_activity = items[:limit]
