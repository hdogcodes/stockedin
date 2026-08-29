"""WTForms form classes (Flask-WTF gives us CSRF protection for free)."""

from datetime import date

from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    FloatField,
    IntegerField,
    PasswordField,
    SelectField,
    SelectMultipleField,
    StringField,
    SubmitField,
    TextAreaField,
    widgets,
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

from constants import PORTFOLIO_GOALS, PORTFOLIO_TAGS, PREDICTION_DIRECTIONS, RISK_LEVELS
from models import User
from prices import ticker_exists


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


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
    strategy = StringField(
        "Strategy (short)", validators=[Optional(), Length(max=120)]
    )
    risk_level = SelectField(
        "Risk level",
        choices=[("", "Not set")] + [(r, r) for r in RISK_LEVELS],
        validators=[Optional()],
    )
    goal = SelectField(
        "Goal",
        choices=[("", "Not set")] + [(g, g) for g in PORTFOLIO_GOALS],
        validators=[Optional()],
    )
    tags = MultiCheckboxField(
        "Tags", choices=[(t, t) for t in PORTFOLIO_TAGS], validators=[Optional()]
    )
    thesis = TextAreaField(
        "Why I invest this way",
        validators=[Optional(), Length(max=1000)],
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
    reasoning = TextAreaField(
        "Why this pick? (optional, shown as an activity update)",
        validators=[Optional(), Length(max=500)],
    )
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


class ProfileForm(FlaskForm):
    bio = TextAreaField("Bio", validators=[Optional(), Length(max=200)])
    university = StringField(
        "University (optional)", validators=[Optional(), Length(max=120)]
    )
    degree = StringField("Degree (optional)", validators=[Optional(), Length(max=120)])
    grad_year = IntegerField(
        "Graduation year (optional)",
        validators=[Optional(), NumberRange(min=1950, max=2100)],
    )
    submit = SubmitField("Save profile")


class PredictionForm(FlaskForm):
    ticker = StringField(
        "Ticker",
        validators=[DataRequired(), Length(max=12)],
        filters=[lambda v: v.strip().upper() if v else v],
    )
    benchmark = StringField(
        "Benchmark",
        default="SPY",
        validators=[DataRequired(), Length(max=12)],
        filters=[lambda v: v.strip().upper() if v else v],
    )
    direction = SelectField(
        "Direction",
        choices=[(d, d.capitalize()) for d in PREDICTION_DIRECTIONS],
        validators=[DataRequired()],
    )
    statement = StringField(
        "Prediction (e.g. \"NVDA will outperform the S&P 500 in 6 months\")",
        validators=[DataRequired(), Length(max=280)],
    )
    target_date = DateField("Target date", validators=[DataRequired()])
    submit = SubmitField("Make prediction")

    def validate_ticker(self, field):
        if not ticker_exists(field.data):
            raise ValidationError("Could not find a price for that ticker.")

    def validate_benchmark(self, field):
        if not ticker_exists(field.data):
            raise ValidationError("Could not find a price for that benchmark ticker.")

    def validate_target_date(self, field):
        if field.data and field.data <= date.today():
            raise ValidationError("Target date must be in the future.")


class GroupForm(FlaskForm):
    name = StringField("Group name", validators=[DataRequired(), Length(max=80)])
    description = TextAreaField(
        "Description", validators=[Optional(), Length(max=300)]
    )
    submit = SubmitField("Create group")


class GroupJoinForm(FlaskForm):
    code = StringField(
        "Invite code",
        validators=[DataRequired(), Length(max=10)],
        filters=[lambda v: v.strip().upper() if v else v],
    )
    submit = SubmitField("Join group")


class GroupInviteForm(FlaskForm):
    username = StringField("Username to invite", validators=[DataRequired(), Length(max=32)])
    submit = SubmitField("Add to group")


class GroupMessageForm(FlaskForm):
    body = StringField("Message", validators=[DataRequired(), Length(max=500)])
    submit = SubmitField("Post")
