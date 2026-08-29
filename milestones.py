"""Auto-detected portfolio milestones (crossing a return threshold), logged
as PortfolioUpdate entries so the activity feed has more than just manual
holding-add notes."""

from extensions import db
from models import PortfolioUpdate

THRESHOLDS = [10, 25, 50, 100, 200]


def check_milestones(portfolio, total_gain_loss_pct):
    if total_gain_loss_pct is None:
        return

    existing = {u.body for u in portfolio.updates if u.kind == "milestone"}
    dirty = False
    for threshold in THRESHOLDS:
        label = f"Crossed +{threshold}% total return"
        if total_gain_loss_pct >= threshold and label not in existing:
            db.session.add(
                PortfolioUpdate(portfolio_id=portfolio.id, kind="milestone", body=label)
            )
            dirty = True

    if dirty:
        db.session.commit()
