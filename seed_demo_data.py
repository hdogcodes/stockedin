"""One-off enrichment script for demo purposes: renames the leftover
test-signup accounts (ssss, asdasd, user1, etc.) into presentable personas
with differently-themed portfolios, diversifies the dave/erin/frank/grace/
heidi group (which all held an identical AAPL/MSFT/NVDA set), adds a new
`hugo` demo account, and populates follows, DMs, comments, a group and a
couple of predictions so the app doesn't look empty on first look.

Safe to re-run: every step checks for existing state first.

Run:
    python seed_demo_data.py
"""

from datetime import date, datetime, timedelta

from app import create_app
from extensions import db
from models import Comment, Follow, Group, GroupMembership, GroupMessage, Holding, Message, Portfolio, Prediction, User


def get_or_none(username):
    return User.query.filter_by(username=username).first()


def rewrite_user(username, *, bio, university=None, degree=None, grad_year=None):
    user = get_or_none(username)
    if user is None:
        return None
    user.bio = bio
    user.university = university
    user.degree = degree
    user.grad_year = grad_year
    return user


def rename_user(old_username, new_username, **fields):
    user = get_or_none(old_username)
    if user is None:
        user = get_or_none(new_username)  # already renamed on a prior run
        if user is None:
            return None
    else:
        if get_or_none(new_username) is None:
            user.username = new_username
            user.email = f"{new_username}@example.com"
    return rewrite_user(new_username, **fields)


def set_portfolio(user, *, title, description, strategy, risk_level, goal, tags, thesis, holdings):
    if user is None:
        return None
    portfolio = user.portfolio
    if portfolio is None:
        portfolio = Portfolio(owner=user, title=title)
        db.session.add(portfolio)
    portfolio.title = title
    portfolio.description = description
    portfolio.strategy = strategy
    portfolio.risk_level = risk_level
    portfolio.goal = goal
    portfolio.tags = ",".join(tags)
    portfolio.thesis = thesis
    db.session.flush()

    Holding.query.filter_by(portfolio_id=portfolio.id).delete()
    for h in holdings:
        db.session.add(
            Holding(
                portfolio_id=portfolio.id,
                ticker=h["ticker"],
                shares=h["shares"],
                buy_price=h["buy_price"],
                buy_date=h["buy_date"],
            )
        )
    return portfolio


def ensure_follow(follower, followed):
    if follower is None or followed is None or follower.id == followed.id:
        return
    exists = Follow.query.filter_by(follower_id=follower.id, followed_id=followed.id).first()
    if not exists:
        db.session.add(Follow(follower_id=follower.id, followed_id=followed.id))


def ensure_message(sender, recipient, body, when):
    if sender is None or recipient is None:
        return
    exists = Message.query.filter_by(sender_id=sender.id, recipient_id=recipient.id, body=body).first()
    if not exists:
        db.session.add(Message(sender_id=sender.id, recipient_id=recipient.id, body=body, created_at=when))


def ensure_comment(user, portfolio, body):
    if user is None or portfolio is None:
        return
    exists = Comment.query.filter_by(user_id=user.id, portfolio_id=portfolio.id, body=body).first()
    if not exists:
        db.session.add(Comment(user_id=user.id, portfolio_id=portfolio.id, body=body))


def ensure_prediction(user, ticker, benchmark, direction, statement, target_date, baseline_ticker, baseline_benchmark):
    if user is None:
        return
    exists = Prediction.query.filter_by(user_id=user.id, statement=statement).first()
    if not exists:
        db.session.add(
            Prediction(
                user_id=user.id,
                ticker=ticker,
                benchmark=benchmark,
                direction=direction,
                statement=statement,
                target_date=target_date,
                baseline_ticker_price=baseline_ticker,
                baseline_benchmark_price=baseline_benchmark,
            )
        )


def seed():
    # ---- 1. hugo: the account to log in and demo with ----
    hugo = get_or_none("hugo")
    if hugo is None:
        hugo = User(username="hugo", email="hugo@example.com")
        hugo.set_password("password")
        db.session.add(hugo)
        db.session.flush()
    rewrite_user(
        "hugo",
        bio="CS senior, all-in on the AI infrastructure trade.",
        university="Stanford",
        degree="B.S. Computer Science",
        grad_year=2025,
    )
    set_portfolio(
        hugo,
        title="AI Infrastructure",
        description="Concentrated bets on the companies building the AI stack.",
        strategy="Picks-and-shovels: chips, cloud, and the infrastructure layer rather than app-layer bets.",
        risk_level="High",
        goal="🚀 High Growth",
        tags=["🚀 Growth", "🤖 AI", "🎓 Student"],
        thesis="AI compute demand is still early. I'd rather own the picks-and-shovels than guess which app wins.",
        holdings=[
            {"ticker": "NVDA", "shares": 10, "buy_price": 450.00, "buy_date": date(2023, 11, 1)},
            {"ticker": "MSFT", "shares": 8, "buy_price": 340.00, "buy_date": date(2023, 6, 1)},
            {"ticker": "AMD", "shares": 15, "buy_price": 110.00, "buy_date": date(2024, 1, 15)},
            {"ticker": "AMZN", "shares": 5, "buy_price": 145.00, "buy_date": date(2024, 3, 1)},
        ],
    )

    # ---- 2. rename the leftover test-signup junk into presentable personas ----
    carol = rewrite_user("carol", bio="Trying to time momentum, mostly losing.")
    set_portfolio(
        carol,
        title="Momentum Plays",
        description="Chases what's moving, cuts losses fast (in theory).",
        strategy="High-turnover momentum names, sized small so a bad week doesn't wreck the month.",
        risk_level="High",
        goal="🚀 High Growth",
        tags=["🚀 Growth"],
        thesis="If it's moving, I'm probably already late — but I keep trying anyway.",
        holdings=[
            {"ticker": "TSLA", "shares": 6, "buy_price": 260.00, "buy_date": date(2024, 4, 10)},
            {"ticker": "COIN", "shares": 8, "buy_price": 190.00, "buy_date": date(2024, 2, 20)},
            {"ticker": "PLTR", "shares": 40, "buy_price": 22.00, "buy_date": date(2024, 5, 5)},
        ],
    )

    mia = rename_user("ssss", "mia", bio="Dividend growth investor. Boring on purpose.")
    set_portfolio(
        mia,
        title="Cashflow First",
        description="Quality dividend payers, reinvested, held forever.",
        strategy="Buy durable dividend growers, reinvest everything, don't touch it for a decade.",
        risk_level="Low",
        goal="💵 Passive Income",
        tags=["💰 Dividend", "🛡️ Low Risk"],
        thesis="I don't need this to 10x. I need it to still be paying me in 20 years.",
        holdings=[
            {"ticker": "KO", "shares": 25, "buy_price": 58.00, "buy_date": date(2022, 9, 1)},
            {"ticker": "PG", "shares": 12, "buy_price": 140.00, "buy_date": date(2022, 11, 1)},
            {"ticker": "JNJ", "shares": 10, "buy_price": 155.00, "buy_date": date(2023, 1, 15)},
        ],
    )

    noah = rename_user("yaya9982", "noah", bio="ESG or nothing.")
    set_portfolio(
        noah,
        title="Clean Energy Bet",
        description="Betting the energy transition is underpriced.",
        strategy="Concentrated in renewables and the electrification supply chain.",
        risk_level="Medium",
        goal="💰 Long-Term Wealth",
        tags=["🌱 Sustainable"],
        thesis="Renewables capex keeps growing while fossil capex shrinks. I want to own that shift, not read about it.",
        holdings=[
            {"ticker": "NEE", "shares": 20, "buy_price": 68.00, "buy_date": date(2023, 3, 1)},
            {"ticker": "ENPH", "shares": 10, "buy_price": 130.00, "buy_date": date(2023, 7, 15)},
            {"ticker": "TSLA", "shares": 4, "buy_price": 220.00, "buy_date": date(2023, 10, 1)},
        ],
    )

    liam = rename_user("asdasd", "liam", bio="Value investor, allergic to hype.")
    set_portfolio(
        liam,
        title="Blue Chip Value",
        description="Boring, profitable, fairly-priced businesses.",
        strategy="Buy quality compounders when the price is reasonable, then wait.",
        risk_level="Low",
        goal="🛡️ Preserve Capital",
        tags=["🛡️ Low Risk"],
        thesis="I'd rather own a good business at a fair price than a great story at any price.",
        holdings=[
            {"ticker": "JPM", "shares": 10, "buy_price": 145.00, "buy_date": date(2023, 2, 1)},
            {"ticker": "V", "shares": 6, "buy_price": 230.00, "buy_date": date(2023, 4, 1)},
            {"ticker": "KO", "shares": 15, "buy_price": 60.00, "buy_date": date(2023, 5, 1)},
        ],
    )

    priya = rename_user(
        "user1", "priya",
        bio="Exchange student, learning to invest for real money for the first time.",
        university="University of Melbourne", degree="B.Com", grad_year=2026,
    )
    set_portfolio(
        priya,
        title="First Portfolio",
        description="Starting simple: a broad index plus a couple of names I actually understand.",
        strategy="Mostly index, a couple of individual names I use every day.",
        risk_level="Low",
        goal="🎓 Education",
        tags=["🎓 Student", "🛡️ Low Risk"],
        thesis="This is money I can't afford to gamble, so step one is just not blowing myself up.",
        holdings=[
            {"ticker": "VTI", "shares": 5, "buy_price": 220.00, "buy_date": date(2024, 2, 1)},
            {"ticker": "AAPL", "shares": 3, "buy_price": 180.00, "buy_date": date(2024, 3, 1)},
            {"ticker": "MSFT", "shares": 2, "buy_price": 400.00, "buy_date": date(2024, 4, 1)},
        ],
    )

    owen = rename_user("user2", "owen", bio="Global macro. Mostly wrong, occasionally right.")
    set_portfolio(
        owen,
        title="Around the World",
        description="Spreads bets across regions instead of betting the farm on the US.",
        strategy="Deliberate non-US tilt alongside a couple of mega-cap anchors.",
        risk_level="Medium",
        goal="💰 Long-Term Wealth",
        tags=["🌎 Global", "🚀 Growth"],
        thesis="The US isn't the only market that compounds. I want exposure outside it too.",
        holdings=[
            {"ticker": "BABA", "shares": 12, "buy_price": 85.00, "buy_date": date(2023, 8, 1)},
            {"ticker": "TSM", "shares": 8, "buy_price": 95.00, "buy_date": date(2023, 9, 1)},
            {"ticker": "ASML", "shares": 3, "buy_price": 650.00, "buy_date": date(2023, 12, 1)},
        ],
    )

    zoe = rename_user("dddddd", "zoe", bio="Tech-heavy and not sorry about it.")
    set_portfolio(
        zoe,
        title="Big Tech Core",
        description="Owns the platforms everyone already depends on.",
        strategy="Mega-cap tech as the core position, rebalanced rarely.",
        risk_level="Medium",
        goal="🚀 High Growth",
        tags=["💻 Technology", "🚀 Growth"],
        thesis="These businesses print cash and I don't need to be clever — I just need to hold.",
        holdings=[
            {"ticker": "GOOGL", "shares": 8, "buy_price": 130.00, "buy_date": date(2023, 5, 1)},
            {"ticker": "META", "shares": 6, "buy_price": 300.00, "buy_date": date(2023, 6, 1)},
            {"ticker": "AMZN", "shares": 7, "buy_price": 140.00, "buy_date": date(2023, 7, 1)},
        ],
    )

    ravi = rename_user(
        "tester", "ravi",
        bio="New to investing. Index funds and patience.",
        university="UNSW", degree="B.Eng", grad_year=2027,
    )
    set_portfolio(
        ravi,
        title="Slow and Steady",
        description="Set it and forget it — broad market index, nothing fancy.",
        strategy="Two funds, dollar-cost averaged, checked once a month at most.",
        risk_level="Low",
        goal="💰 Long-Term Wealth",
        tags=["🛡️ Low Risk", "🎓 Student"],
        thesis="I don't trust myself to pick stocks yet, so I'm not going to pretend I can.",
        holdings=[
            {"ticker": "VOO", "shares": 4, "buy_price": 420.00, "buy_date": date(2024, 1, 1)},
            {"ticker": "BND", "shares": 10, "buy_price": 72.00, "buy_date": date(2024, 1, 1)},
        ],
    )

    # ---- 3. diversify dave/erin/frank/grace/heidi (were an identical set) ----
    dave = rewrite_user("dave", bio="Digital-asset infrastructure, mostly.", university="MIT")
    set_portfolio(
        dave,
        title="Crypto-Adjacent Growth",
        description="Betting on the infrastructure around digital assets, not the coins themselves.",
        strategy="Public companies with direct crypto/AI infrastructure exposure.",
        risk_level="High",
        goal="🚀 High Growth",
        tags=["🚀 Growth", "🤖 AI"],
        thesis="I'd rather own regulated, audited companies riding this wave than hold the coins directly.",
        holdings=[
            {"ticker": "COIN", "shares": 6, "buy_price": 150.00, "buy_date": date(2023, 10, 1)},
            {"ticker": "MSTR", "shares": 3, "buy_price": 400.00, "buy_date": date(2024, 1, 1)},
            {"ticker": "NVDA", "shares": 5, "buy_price": 480.00, "buy_date": date(2024, 2, 1)},
        ],
    )

    erin = rewrite_user("erin", bio="Sustainable investing with a global tilt.")
    set_portfolio(
        erin,
        title="Sustainable & Global",
        description="Clean energy plus non-US semiconductor exposure.",
        strategy="ESG-screened growth names, deliberately not US-only.",
        risk_level="Medium",
        goal="💰 Long-Term Wealth",
        tags=["🌱 Sustainable", "🌎 Global"],
        thesis="Sustainability and diversification aren't in tension — I want both in the same portfolio.",
        holdings=[
            {"ticker": "ASML", "shares": 2, "buy_price": 600.00, "buy_date": date(2023, 6, 1)},
            {"ticker": "NEE", "shares": 15, "buy_price": 65.00, "buy_date": date(2023, 4, 1)},
            {"ticker": "MSFT", "shares": 4, "buy_price": 320.00, "buy_date": date(2023, 5, 1)},
        ],
    )

    frank = rewrite_user("frank", bio="Dividend income, full stop.")
    set_portfolio(
        frank,
        title="Dividend Machine",
        description="Cashflow-focused, low drama.",
        strategy="High-quality dividend payers across a few different sectors.",
        risk_level="Low",
        goal="💵 Passive Income",
        tags=["💰 Dividend", "🛡️ Low Risk"],
        thesis="I optimize for the deposit hitting my account, not for bragging rights on returns.",
        holdings=[
            {"ticker": "JNJ", "shares": 8, "buy_price": 150.00, "buy_date": date(2022, 10, 1)},
            {"ticker": "VZ", "shares": 30, "buy_price": 38.00, "buy_date": date(2022, 12, 1)},
            {"ticker": "PG", "shares": 6, "buy_price": 135.00, "buy_date": date(2023, 2, 1)},
        ],
    )

    grace = rewrite_user("grace", bio="Index and chill.")
    set_portfolio(
        grace,
        title="Index & Chill",
        description="Broad market, low cost, minimal effort.",
        strategy="Two or three funds, nothing else. Rebalance once a year.",
        risk_level="Low",
        goal="🛡️ Preserve Capital",
        tags=["🛡️ Low Risk", "🌎 Global"],
        thesis="Picking stocks is a hobby. My retirement account is not the place for hobbies.",
        holdings=[
            {"ticker": "VTI", "shares": 12, "buy_price": 210.00, "buy_date": date(2022, 6, 1)},
            {"ticker": "VOO", "shares": 6, "buy_price": 380.00, "buy_date": date(2022, 8, 1)},
            {"ticker": "BND", "shares": 15, "buy_price": 75.00, "buy_date": date(2022, 6, 1)},
        ],
    )

    heidi = rewrite_user("heidi", bio="Concentrated on the AI chip trade.")
    set_portfolio(
        heidi,
        title="Concentrated AI Bet",
        description="A small number of names, sized big.",
        strategy="High conviction, low diversification, on purpose.",
        risk_level="High",
        goal="🚀 High Growth",
        tags=["🤖 AI", "🚀 Growth"],
        thesis="Diversification is protection against not knowing what you own. I know exactly what I own.",
        holdings=[
            {"ticker": "NVDA", "shares": 6, "buy_price": 460.00, "buy_date": date(2023, 9, 1)},
            {"ticker": "AMD", "shares": 12, "buy_price": 105.00, "buy_date": date(2023, 11, 1)},
            {"ticker": "MSFT", "shares": 3, "buy_price": 350.00, "buy_date": date(2024, 1, 1)},
        ],
    )

    db.session.commit()

    # ---- 4. social graph: wire hugo in ----
    for target in (zoe, heidi, dave, noah, priya):
        ensure_follow(hugo, target)
    for back in (zoe, heidi, priya):  # mutual -> DM-eligible
        ensure_follow(back, hugo)
    # a few extra edges among the renamed personas for a less star-shaped graph
    ensure_follow(mia, liam)
    ensure_follow(liam, mia)
    ensure_follow(zoe, heidi)
    ensure_follow(heidi, zoe)
    ensure_follow(carol, dave)
    ensure_follow(owen, erin)
    db.session.commit()

    # ---- 5. DM conversations ----
    now = datetime.utcnow()
    if zoe:
        ensure_message(hugo, zoe, "hey! saw you're all-in on the big tech names, curious why no NVDA though", now - timedelta(days=3, hours=2))
        ensure_message(zoe, hugo, "mostly cause I already get AI exposure through GOOGL/AMZN/META tbh, didn't want 4 overlapping bets", now - timedelta(days=3, hours=1))
        ensure_message(hugo, zoe, "fair, I'm more concentrated than that. NVDA + AMD is like 60% of my book rn", now - timedelta(days=3))
        ensure_message(zoe, hugo, "that's brave lol. how's it held up", now - timedelta(days=2, hours=20))
        ensure_message(hugo, zoe, "swings a lot but net been good so far, we'll see", now - timedelta(days=2, hours=19))
    if heidi:
        ensure_message(heidi, hugo, "your AI infra portfolio and mine are basically twins haha", now - timedelta(days=1, hours=5))
        ensure_message(hugo, heidi, "right?? great minds. you doing AMD too or just NVDA/MSFT", now - timedelta(days=1, hours=4))
        ensure_message(heidi, hugo, "AMD MSFT NVDA, no AMZN though. thinking about adding it", now - timedelta(days=1, hours=3))
        ensure_message(hugo, heidi, "amzn's been the quiet compounder for me, worth a look", now - timedelta(days=1, hours=2))
    if priya:
        ensure_message(priya, hugo, "hi! new here, saw you're also studying cs — any tips for someone just starting to invest?", now - timedelta(hours=10))
        ensure_message(hugo, priya, "honestly what you're doing already (mostly index + names you understand) is the right start", now - timedelta(hours=9))
        ensure_message(hugo, priya, "I went too concentrated too early, wouldn't recommend that part lol", now - timedelta(hours=9))
        ensure_message(priya, hugo, "good to know, thank you!! will keep it simple for now", now - timedelta(hours=8))
    db.session.commit()

    # ---- 6. comments on portfolios ----
    if hugo and hugo.portfolio:
        ensure_comment(zoe, hugo.portfolio, "concentrated but I respect the conviction")
        ensure_comment(heidi, hugo.portfolio, "basically my portfolio's twin")
    if zoe and zoe.portfolio:
        ensure_comment(hugo, zoe.portfolio, "solid core, surprised there's no NVDA in here")
    if mia and mia.portfolio:
        ensure_comment(frank, mia.portfolio, "love a good dividend portfolio, KO is a staple for me too")
    if noah and noah.portfolio:
        ensure_comment(erin, noah.portfolio, "ENPH has been rough lately but I like the thesis long term")
    if grace and grace.portfolio:
        ensure_comment(ravi, grace.portfolio, "this is basically the portfolio I'm trying to build")
    db.session.commit()

    # ---- 7. a couple more predictions for variety ----
    ensure_prediction(
        hugo, "NVDA", "SPY", "outperform",
        "NVDA will outperform the S&P 500 over the next 6 months",
        date.today() + timedelta(days=180), 118.0, 560.0,
    )
    ensure_prediction(
        zoe, "GOOGL", "SPY", "outperform",
        "GOOGL will outperform the S&P 500 by year end",
        date.today() + timedelta(days=90), 175.0, 560.0,
    )
    ensure_prediction(
        noah, "NEE", "SPY", "outperform",
        "NEE will outperform the S&P 500 over the next year",
        date.today() + timedelta(days=365), 72.0, 560.0,
    )
    db.session.commit()

    # ---- 8. a themed group for hugo ----
    group = Group.query.filter_by(name="AI Infra Club").first()
    if group is None:
        group = Group(
            name="AI Infra Club",
            description="Tracking the AI infrastructure trade together.",
            code="AIINFRA",
            owner_id=hugo.id,
        )
        db.session.add(group)
        db.session.flush()
        db.session.add(GroupMembership(group_id=group.id, user_id=hugo.id))
    for member in (zoe, heidi):
        if member and not group.has_member(member):
            db.session.add(GroupMembership(group_id=group.id, user_id=member.id))
    db.session.commit()

    if not GroupMessage.query.filter_by(group_id=group.id).first():
        db.session.add(GroupMessage(group_id=group.id, user_id=hugo.id, body="Welcome — figured we should compare notes since we're all in the same trade."))
        db.session.add(GroupMessage(group_id=group.id, user_id=heidi.id, body="Been meaning to make a group like this lol, in"))
        db.session.add(GroupMessage(group_id=group.id, user_id=zoe.id, body="same, curious to see who's up more at the end of the year"))
        db.session.commit()

    print("Demo data seeded. Log in as hugo / password to explore.")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        seed()
