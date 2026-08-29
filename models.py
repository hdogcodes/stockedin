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

    @property
    def like_count(self):
        return len(self.likes)

    def is_liked_by(self, user):
        if user is None or not user.is_authenticated:
            return False
        return any(like.user_id == user.id for like in self.likes)

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


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
