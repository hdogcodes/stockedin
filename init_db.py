"""One-off setup script: creates tables and seeds two demo users.

Run once after installing dependencies:
    python init_db.py
"""

from datetime import date

from app import create_app
from extensions import db
from models import Follow, Holding, Portfolio, User


def seed():
    if User.query.first() is not None:
        print("Database already has data — skipping seed.")
        return

    alice = User(username="alice", email="alice@example.com", bio="Long-term tech investor.")
    alice.set_password("password123")

    bob = User(username="bob", email="bob@example.com", bio="Dividends and index funds.")
    bob.set_password("password123")

    db.session.add_all([alice, bob])
    db.session.flush()  # assigns ids without committing yet

    alice_portfolio = Portfolio(
        owner=alice, title="Tech Growth", description="Betting on big tech long term."
    )
    bob_portfolio = Portfolio(
        owner=bob, title="Steady Income", description="Boring and diversified, on purpose."
    )
    db.session.add_all([alice_portfolio, bob_portfolio])
    db.session.flush()

    db.session.add_all(
        [
            Holding(
                portfolio=alice_portfolio,
                ticker="AAPL",
                shares=10,
                buy_price=150.00,
                buy_date=date(2023, 1, 15),
            ),
            Holding(
                portfolio=alice_portfolio,
                ticker="MSFT",
                shares=5,
                buy_price=280.00,
                buy_date=date(2023, 3, 1),
            ),
            Holding(
                portfolio=bob_portfolio,
                ticker="VTI",
                shares=20,
                buy_price=200.00,
                buy_date=date(2022, 6, 10),
            ),
            Holding(
                portfolio=bob_portfolio,
                ticker="JNJ",
                shares=8,
                buy_price=160.00,
                buy_date=date(2022, 11, 5),
            ),
        ]
    )

    db.session.add(Follow(follower_id=bob.id, followed_id=alice.id))

    db.session.commit()
    print("Seeded demo users: alice/password123, bob/password123")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
        seed()
