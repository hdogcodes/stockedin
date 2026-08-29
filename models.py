"""Database models for the portfolio social network."""

from datetime import date, datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    bio = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # All optional — "student investor" identity, not a requirement to sign up.
    university = db.Column(db.String(120), index=True)
    degree = db.Column(db.String(120))
    grad_year = db.Column(db.Integer)

    # Each user has at most one portfolio (uselist=False makes this one-to-one).
    portfolio = db.relationship(
        "Portfolio",
        back_populates="owner",
        uselist=False,
        cascade="all, delete-orphan",
    )
    likes = db.relationship("Like", back_populates="user", cascade="all, delete-orphan")
    comments = db.relationship(
        "Comment", back_populates="user", cascade="all, delete-orphan"
    )
    predictions = db.relationship(
        "Prediction",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="Prediction.created_at.desc()",
    )
    group_memberships = db.relationship(
        "GroupMembership", back_populates="user", cascade="all, delete-orphan"
    )

    # Follow rows where this user is the one doing the following.
    following = db.relationship(
        "Follow",
        foreign_keys="Follow.follower_id",
        back_populates="follower",
        cascade="all, delete-orphan",
    )
    # Follow rows where this user is the one being followed.
    followers = db.relationship(
        "Follow",
        foreign_keys="Follow.followed_id",
        back_populates="followed",
        cascade="all, delete-orphan",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_following(self, other):
        if other is None:
            return False
        return (
            Follow.query.filter_by(follower_id=self.id, followed_id=other.id).first()
            is not None
        )

    def is_mutual_with(self, other):
        """True if each follows the other — the bar for being able to DM."""
        if other is None or other.id == self.id:
            return False
        return self.is_following(other) and other.is_following(self)

    @property
    def mutual_friends(self):
        """Users this account follows AND is followed back by, i.e. who it can DM."""
        following_ids = {f.followed_id for f in self.following}
        follower_ids = {f.follower_id for f in self.followers}
        mutual_ids = following_ids & follower_ids
        if not mutual_ids:
            return []
        return User.query.filter(User.id.in_(mutual_ids)).order_by(User.username).all()

    @property
    def unread_message_count(self):
        return Message.query.filter_by(recipient_id=self.id, read_at=None).count()

    @property
    def is_student(self):
        return bool(self.university)

    @property
    def groups(self):
        return [m.group for m in self.group_memberships]

    @property
    def prediction_accuracy(self):
        """(correct, total_resolved) — None share when nothing's resolved yet."""
        resolved = [p for p in self.predictions if p.status != "Pending"]
        if not resolved:
            return None
        correct = sum(1 for p in resolved if p.status == "Correct")
        return round(correct / len(resolved) * 100)

    @property
    def following_count(self):
        return Follow.query.filter_by(follower_id=self.id).count()

    @property
    def followers_count(self):
        return Follow.query.filter_by(followed_id=self.id).count()

    def __repr__(self):
        return f"<User {self.username}>"


class Portfolio(db.Model):
    """A user's portfolio — the equivalent of an Instagram post."""

    __tablename__ = "portfolios"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False
    )
    title = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Strategy/identity fields — all optional, upgrade a bare holdings list
    # into something you can discover and follow for its reasoning.
    strategy = db.Column(db.String(120))
    risk_level = db.Column(db.String(20))
    goal = db.Column(db.String(40))
    thesis = db.Column(db.Text)
    # Comma-separated tag strings (e.g. "🚀 Growth,🤖 AI") rather than a
    # separate join table — the tag set is small and fixed, so filtering in
    # Python is simple and plenty fast at this app's scale.
    tags = db.Column(db.String(200))

    owner = db.relationship("User", back_populates="portfolio")
    holdings = db.relationship(
        "Holding",
        back_populates="portfolio",
        cascade="all, delete-orphan",
        order_by="Holding.ticker",
    )
    likes = db.relationship(
        "Like", back_populates="portfolio", cascade="all, delete-orphan"
    )
    comments = db.relationship(
        "Comment",
        back_populates="portfolio",
        cascade="all, delete-orphan",
        order_by="Comment.created_at",
    )
    snapshots = db.relationship(
        "PortfolioSnapshot",
        back_populates="portfolio",
        cascade="all, delete-orphan",
        order_by="PortfolioSnapshot.date",
    )
    updates = db.relationship(
        "PortfolioUpdate",
        back_populates="portfolio",
        cascade="all, delete-orphan",
        order_by="PortfolioUpdate.created_at.desc()",
    )

    @property
    def like_count(self):
        return len(self.likes)

    def is_liked_by(self, user):
        if user is None or not user.is_authenticated:
            return False
        return any(like.user_id == user.id for like in self.likes)

    @property
    def tag_list(self):
        return [t for t in (self.tags or "").split(",") if t]

    @property
    def personality(self):
        from personality import compute_personality
        return compute_personality(self)

    def __repr__(self):
        return f"<Portfolio {self.title!r} of user {self.user_id}>"


class Holding(db.Model):
    __tablename__ = "holdings"

    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(
        db.Integer, db.ForeignKey("portfolios.id"), nullable=False
    )
    ticker = db.Column(db.String(12), nullable=False)
    shares = db.Column(db.Float, nullable=False)
    buy_price = db.Column(db.Float, nullable=False)
    buy_date = db.Column(db.Date, default=date.today, nullable=False)

    portfolio = db.relationship("Portfolio", back_populates="holdings")

    @property
    def cost_basis(self):
        return self.shares * self.buy_price

    def __repr__(self):
        return f"<Holding {self.ticker} x{self.shares}>"


class Follow(db.Model):
    """Association object so a follow can carry its own created_at."""

    __tablename__ = "follows"

    follower_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    follower = db.relationship(
        "User", foreign_keys=[follower_id], back_populates="following"
    )
    followed = db.relationship(
        "User", foreign_keys=[followed_id], back_populates="followers"
    )

    __table_args__ = (
        db.CheckConstraint("follower_id != followed_id", name="no_self_follow"),
    )


class Like(db.Model):
    __tablename__ = "likes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    portfolio_id = db.Column(
        db.Integer, db.ForeignKey("portfolios.id"), nullable=False
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="likes")
    portfolio = db.relationship("Portfolio", back_populates="likes")

    __table_args__ = (
        db.UniqueConstraint("user_id", "portfolio_id", name="one_like_per_user"),
    )


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    portfolio_id = db.Column(
        db.Integer, db.ForeignKey("portfolios.id"), nullable=False
    )
    body = db.Column(db.String(280), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="comments")
    portfolio = db.relationship("Portfolio", back_populates="comments")


class PortfolioSnapshot(db.Model):
    """One recorded total-value data point for a portfolio on a given day.

    Recorded (upserted) each time a portfolio is viewed with live prices
    available, so the growth chart fills in naturally over time rather than
    needing a separate cron job.
    """

    __tablename__ = "portfolio_snapshots"

    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(
        db.Integer, db.ForeignKey("portfolios.id"), nullable=False
    )
    date = db.Column(db.Date, nullable=False)
    total_value = db.Column(db.Float, nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    portfolio = db.relationship("Portfolio", back_populates="snapshots")

    __table_args__ = (
        db.UniqueConstraint("portfolio_id", "date", name="one_snapshot_per_day"),
    )


class BenchmarkSnapshot(db.Model):
    """Same idea as PortfolioSnapshot but for a market index/ETF ticker
    (default SPY), so "your return vs. the S&P 500" has real recorded data
    to compare against instead of needing historical-candle API access."""

    __tablename__ = "benchmark_snapshots"

    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(12), nullable=False)
    date = db.Column(db.Date, nullable=False)
    price = db.Column(db.Float, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("ticker", "date", name="one_benchmark_snapshot_per_day"),
    )


class PortfolioUpdate(db.Model):
    """A timeline entry for a portfolio: a holding added (with optional
    reasoning), an auto-detected milestone, or a free-text note. Powers the
    "portfolio activity" feed alongside likes/comments."""

    __tablename__ = "portfolio_updates"

    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(
        db.Integer, db.ForeignKey("portfolios.id"), nullable=False
    )
    kind = db.Column(db.String(20), nullable=False)  # holding_added / milestone / note
    ticker = db.Column(db.String(12))
    body = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    portfolio = db.relationship("Portfolio", back_populates="updates")


class Prediction(db.Model):
    """A trackable, resolvable call: "<ticker> will <direction> <benchmark>
    by <target_date>". Baseline prices are captured at creation time;
    resolution (Correct/Incorrect) is computed lazily once target_date has
    passed, using live prices at that point — see predictions.py."""

    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    ticker = db.Column(db.String(12), nullable=False)
    benchmark = db.Column(db.String(12), nullable=False, default="SPY")
    direction = db.Column(db.String(12), nullable=False, default="outperform")
    statement = db.Column(db.String(280), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    target_date = db.Column(db.Date, nullable=False)

    baseline_ticker_price = db.Column(db.Float)
    baseline_benchmark_price = db.Column(db.Float)

    status = db.Column(db.String(12), nullable=False, default="Pending")
    resolved_at = db.Column(db.DateTime)
    resolved_ticker_price = db.Column(db.Float)
    resolved_benchmark_price = db.Column(db.Float)

    user = db.relationship("User", back_populates="predictions")


class Group(db.Model):
    """A private group of friends who can see each other's portfolios,
    discuss, and compare performance on a leaderboard."""

    __tablename__ = "groups"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(300))
    code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    owner = db.relationship("User", foreign_keys=[owner_id])
    memberships = db.relationship(
        "GroupMembership",
        back_populates="group",
        cascade="all, delete-orphan",
        order_by="GroupMembership.joined_at",
    )
    messages = db.relationship(
        "GroupMessage",
        back_populates="group",
        cascade="all, delete-orphan",
        order_by="GroupMessage.created_at",
    )

    @property
    def members(self):
        return [m.user for m in self.memberships]

    def has_member(self, user):
        return user is not None and any(m.user_id == user.id for m in self.memberships)


class GroupMembership(db.Model):
    __tablename__ = "group_memberships"

    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    group = db.relationship("Group", back_populates="memberships")
    user = db.relationship("User", back_populates="group_memberships")


class GroupMessage(db.Model):
    __tablename__ = "group_messages"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    body = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    group = db.relationship("Group", back_populates="messages")
    user = db.relationship("User")


class Message(db.Model):
    """A direct message. Only exchanged between users who mutually follow
    each other — enforced in the route, not here."""

    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    body = db.Column(db.String(1000), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    read_at = db.Column(db.DateTime)

    sender = db.relationship("User", foreign_keys=[sender_id])
    recipient = db.relationship("User", foreign_keys=[recipient_id])


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
