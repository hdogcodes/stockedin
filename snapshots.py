"""Portfolio value-over-time tracking, backing the growth line chart.

There's no historical price API call involved — we don't have a budget for
fetching daily candles per holding. Instead each portfolio view upserts a
"today" data point (see record_snapshot), so the real history builds up
naturally the more the app gets used. To avoid a chart with a single dot on
day one, get_chart_series() also seeds a synthetic starting point at the
portfolio's earliest buy date, valued at cost basis — a reasonable "this is
what you put in" anchor that the real, price-based snapshots grow away from.
"""

from datetime import date

from extensions import db
from models import PortfolioSnapshot


def record_snapshot(portfolio, total_value):
    """Upsert today's total-value data point. No-ops if total_value is None
    (prices unavailable) so a bad reading never overwrites a good one."""
    if total_value is None:
        return

    today = date.today()
    existing = PortfolioSnapshot.query.filter_by(
        portfolio_id=portfolio.id, date=today
    ).first()
    if existing:
        existing.total_value = total_value
    else:
        db.session.add(
            PortfolioSnapshot(portfolio_id=portfolio.id, date=today, total_value=total_value)
        )
    db.session.commit()


def get_chart_series(portfolio):
    """Return [{date, value}, ...] sorted oldest to newest for the chart.

    Empty if the portfolio has no holdings and no recorded snapshots yet.
    """
    points = {}

    earliest_buy = min((h.buy_date for h in portfolio.holdings), default=None)
    if earliest_buy is not None:
        cost_basis = sum(h.cost_basis for h in portfolio.holdings)
        points[earliest_buy] = cost_basis

    for snap in portfolio.snapshots:
        points[snap.date] = snap.total_value

    return [
        {"date": d.strftime("%Y-%m-%d"), "value": round(v, 2)}
        for d, v in sorted(points.items())
    ]
