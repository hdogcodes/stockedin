"""Prediction creation and lazy resolution.

Resolution happens whenever predictions are viewed (profile page, etc.)
rather than on a schedule — same "compute on view" pattern as portfolio
snapshots. A pending prediction whose target_date has passed gets resolved
against live prices at that moment; nothing changes for predictions still
pending or already resolved.
"""

from datetime import date, datetime

from extensions import db
from prices import get_quote


def resolve_due_predictions(predictions):
    """Resolve any Pending prediction in the given list whose target_date
    has passed. Mutates and commits; returns the same list for convenience.
    """
    today = date.today()
    dirty = False

    for pred in predictions:
        if pred.status != "Pending" or pred.target_date > today:
            continue

        ticker_quote = get_quote(pred.ticker)
        benchmark_quote = get_quote(pred.benchmark)
        if ticker_quote is None or benchmark_quote is None:
            continue  # try again next time it's viewed

        if not pred.baseline_ticker_price or not pred.baseline_benchmark_price:
            continue  # baseline was never captured — leave pending

        ticker_return = (
            (ticker_quote["price"] - pred.baseline_ticker_price)
            / pred.baseline_ticker_price
        )
        benchmark_return = (
            (benchmark_quote["price"] - pred.baseline_benchmark_price)
            / pred.baseline_benchmark_price
        )

        ticker_ahead = ticker_return > benchmark_return
        correct = ticker_ahead if pred.direction == "outperform" else not ticker_ahead

        pred.status = "Correct" if correct else "Incorrect"
        pred.resolved_at = datetime.utcnow()
        pred.resolved_ticker_price = ticker_quote["price"]
        pred.resolved_benchmark_price = benchmark_quote["price"]
        dirty = True

    if dirty:
        db.session.commit()

    return predictions
