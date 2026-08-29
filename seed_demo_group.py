"""Creates 5 demo users, makes them all follow each other, and gives each
a portfolio holding 5 shares of AAPL, 5 of MSFT, and 5 of NVDA.

Run:
    python seed_demo_group.py
"""

from datetime import date

from app import create_app
from extensions import db
from models import Follow, Holding, Portfolio, User

USERNAMES = ["dave", "erin", "frank", "grace", "heidi"]
PASSWORD = "password123"

# Reasonable flat buy prices for demo purposes; live current price/value is
# still fetched fresh from the price API whenever a portfolio is rendered.
HOLDINGS = [
    {"ticker": "AAPL", "shares": 5, "buy_price": 190.00, "buy_date": date(2024, 1, 15)},
    {"ticker": "MSFT", "shares": 5, "buy_price": 380.00, "buy_date": date(2024, 2, 1)},
    {"ticker": "NVDA", "shares": 5, "buy_price": 500.00, "buy_date": date(2024, 3, 1)},
]


def seed():
    users = []
    for username in USERNAMES:
        existing = User.query.filter_by(username=username).first()
        if existing:
            print(f"{username} already exists — reusing.")
            users.append(existing)
            continue

        user = User(
            username=username,
            email=f"{username}@example.com",
            bio=f"{username.capitalize()}'s stock portfolio.",
        )
        user.set_password(PASSWORD)
        db.session.add(user)
        users.append(user)

    db.session.flush()  # assign ids

    for user in users:
        if user.portfolio is not None:
            continue
        portfolio = Portfolio(
            owner=user,
            title=f"{user.username.capitalize()}'s Portfolio",
            description="Equal parts Apple, Microsoft, and Nvidia.",
        )
        db.session.add(portfolio)
        db.session.flush()

        for h in HOLDINGS:
            db.session.add(
                Holding(
                    portfolio=portfolio,
                    ticker=h["ticker"],
                    shares=h["shares"],
                    buy_price=h["buy_price"],
                    buy_date=h["buy_date"],
                )
            )

    # Everyone follows everyone else in the group.
    for follower in users:
        for followed in users:
            if follower.id == followed.id:
                continue
            already = Follow.query.filter_by(
                follower_id=follower.id, followed_id=followed.id
            ).first()
            if not already:
                db.session.add(Follow(follower_id=follower.id, followed_id=followed.id))

    db.session.commit()
    print(f"Done. Users: {', '.join(USERNAMES)} (password: {PASSWORD})")
    print("Each holds 5 AAPL / 5 MSFT / 5 NVDA and follows the other four.")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        seed()
