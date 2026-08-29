"""WTForms form classes (Flask-WTF gives us CSRF protection for free)."""

from datetime import date

from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    FloatField,
    PasswordField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    NumberRange,
    Optional,
    Regexp,
    ValidationError,
)

from models import User
from prices import ticker_exists


class SignupForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(min=3, max=32),
            Regexp(
                r"^[A-Za-z0-9_]+$",
                message="Letters, numbers and underscores only.",
            ),
        ],
    )
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    bio = TextAreaField("Bio (optional)", validators=[Optional(), Length(max=200)])
    submit = SubmitField("Create account")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("That username is taken.")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError("That email is already registered.")


class LoginForm(FlaskForm):
    username = StringField("Username or email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log in")


class PortfolioForm(FlaskForm):
    title = StringField(
        "Portfolio name",
        validators=[DataRequired(), Length(max=80)],
    )
    description = TextAreaField(
        "Description", validators=[Optional(), Length(max=300)]
    )
    submit = SubmitField("Save")


class HoldingForm(FlaskForm):
    ticker = StringField(
        "Ticker",
        validators=[DataRequired(), Length(max=12)],
        filters=[lambda value: value.strip().upper() if value else value],
    )
    shares = FloatField(
        "Shares", validators=[DataRequired(), NumberRange(min=0.0001)]
    )
    buy_price = FloatField(
        "Buy price ($)", validators=[DataRequired(), NumberRange(min=0.0001)]
    )
    buy_date = DateField("Buy date", default=date.today, validators=[DataRequired()])
    submit = SubmitField("Add holding")

    def validate_ticker(self, field):
        # Confirm the symbol is real before we save it, so typos surface here
        # rather than as a permanently broken row in the portfolio.
        if not ticker_exists(field.data):
            raise ValidationError(
                "Could not find a price for that ticker. Check the symbol and try again."
            )

    def validate_buy_date(self, field):
        if field.data and field.data > date.today():
            raise ValidationError("Buy date cannot be in the future.")


class CommentForm(FlaskForm):
    body = TextAreaField(
        "Comment", validators=[DataRequired(), Length(max=280)]
    )
    submit = SubmitField("Post")


class MessageForm(FlaskForm):
    body = TextAreaField(
        "Message", validators=[DataRequired(), Length(max=1000)]
    )
    submit = SubmitField("Send")
