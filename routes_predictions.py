"""Trackable predictions: create your own, resolution happens on view."""

from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from extensions import db
from forms import PredictionForm
from models import Prediction
from prices import get_quote


@login_required
def prediction_new():
    if current_user.portfolio is None:
        flash("Create your portfolio first.", "error")
        return redirect(url_for("portfolio_new"))

    form = PredictionForm()
    if form.validate_on_submit():
        ticker_quote = get_quote(form.ticker.data)
        benchmark_quote = get_quote(form.benchmark.data)
        prediction = Prediction(
            user_id=current_user.id,
            ticker=form.ticker.data,
            benchmark=form.benchmark.data,
            direction=form.direction.data,
            statement=form.statement.data,
            target_date=form.target_date.data,
            baseline_ticker_price=ticker_quote["price"] if ticker_quote else None,
            baseline_benchmark_price=benchmark_quote["price"] if benchmark_quote else None,
        )
        db.session.add(prediction)
        db.session.commit()
        flash("Prediction saved — check back after the target date.", "success")
        return redirect(url_for("profile", username=current_user.username))

    return render_template("prediction_form.html", form=form)


def register(app):
    app.add_url_rule(
        "/predictions/new", view_func=prediction_new, methods=["GET", "POST"]
    )
