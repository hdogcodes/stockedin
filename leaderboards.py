"""Feed leaderboard data: top-moving stocks, most-held stocks, and the
best-performing portfolios on the platform.

Scored across every portfolio/holding in the app rather than just the
current user's friends — with only a handful of demo accounts, scoping this
to "your network" would usually come back nearly empty. Everything here is
read-only and cheap: prices are already cached by prices.py, and the holding
counts are a single grouped query.
"""

from sqlalchemy import func

from extensions import db
from models import Holding, Portfolio
from prices import WATCHLIST_TICKERS, attach_stats, prefetch_quotes, get_quote

LEADERBOARD_SIZE = 5


def top_moving_stocks(limit=LEADERBOARD_SIZE):
    """Tickers actually held on the platform (plus the watchlist, so there's
    always something to show), ranked by today's % change."""
    held_tickers = {t for (t,) in db.session.query(Holding.ticker).distinct()}
    tickers = held_tickers | set(WATCHLIST_TICKERS)
    prefetch_quotes(tickers)

    rows = []
    for ticker in tickers:
        quote = get_quote(ticker)
        if quote is not None and quote["day_change_pct"] is not None:
            rows.append({"ticker": ticker, "day_change_pct": quote["day_change_pct"], "price": quote["price"]})

    rows.sort(key=lambda r: r["day_change_pct"], reverse=True)
    return rows[:limit]


def most_held_stocks(limit=LEADERBOARD_SIZE):
    """Tickers ranked by how many distinct portfolios hold them."""
    rows = (
        db.session.query(Holding.ticker, func.count(func.distinct(Holding.portfolio_id)))
        .group_by(Holding.ticker)
        .order_by(func.count(func.distinct(Holding.portfolio_id)).desc(), Holding.ticker)
        .limit(limit)
        .all()
    )
    return [{"ticker": ticker, "holder_count": count} for ticker, count in rows]


def top_portfolios(limit=LEADERBOARD_SIZE):
    """Portfolios ranked by total gain/loss %, best first."""
    portfolios = Portfolio.query.all()
    attach_stats(portfolios)

    rows = []
    for p in portfolios:
        pct = p.stats.get("total_gain_loss_pct")
        if pct is not None:
            rows.append(
                {
                    "username": p.owner.username,
                    "title": p.title,
                    "gain_loss_pct": pct,
                    "gain_loss": p.stats["total_gain_loss"],
                }
            )

    rows.sort(key=lambda r: r["gain_loss_pct"], reverse=True)
    return rows[:limit]
