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

from constants import DEFAULT_BENCHMARK
from extensions import db
from models import BenchmarkSnapshot, PortfolioSnapshot
from prices import get_quote


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


def get_tracking_duration_days(portfolio):
    """Days since the first recorded snapshot — the "verifiable" part of the
    track record, as opposed to the earliest (unverifiable, self-reported)
    buy date on a holding."""
    if not portfolio.snapshots:
        return 0
    return (date.today() - portfolio.snapshots[0].date).days


def record_benchmark_snapshot(ticker=DEFAULT_BENCHMARK):
    """Same upsert-today's-value pattern as record_snapshot, for a market
    index/ETF ticker. Builds up real historical data for benchmark
    comparison going forward, since Finnhub's free tier doesn't give us
    historical candles to backfill with."""
    quote = get_quote(ticker)
    if quote is None:
        return

    today = date.today()
    existing = BenchmarkSnapshot.query.filter_by(ticker=ticker, date=today).first()
    if existing:
        existing.price = quote["price"]
    else:
        db.session.add(BenchmarkSnapshot(ticker=ticker, date=today, price=quote["price"]))
    db.session.commit()


def get_benchmark_return_pct(since_date, ticker=DEFAULT_BENCHMARK):
    """% change in the benchmark's recorded price from since_date to the
    most recent snapshot. None if we don't have at least two points yet."""
    rows = (
        BenchmarkSnapshot.query.filter_by(ticker=ticker)
        .filter(BenchmarkSnapshot.date >= since_date)
        .order_by(BenchmarkSnapshot.date)
        .all()
    )
    if len(rows) < 2:
        return None
    start, end = rows[0].price, rows[-1].price
    if not start:
        return None
    return (end - start) / start * 100
