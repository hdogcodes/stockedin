"""Create/edit portfolio and add/remove holding views. Owner-only mutations."""

from flask import abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from extensions import db
from forms import HoldingForm, PortfolioForm
from models import Holding, Portfolio


@login_required
def portfolio_new():
    if current_user.portfolio is not None:
        return redirect(url_for("portfolio_edit"))

    form = PortfolioForm()
    if form.validate_on_submit():
        portfolio = Portfolio(
            owner=current_user, title=form.title.data, description=form.description.data
        )
        db.session.add(portfolio)
        db.session.commit()
        flash("Portfolio created — now add a holding.", "success")
        return redirect(url_for("holding_new"))

    return render_template("portfolio_form.html", form=form, mode="new")


@login_required
def portfolio_edit():
    portfolio = current_user.portfolio
    if portfolio is None:
        return redirect(url_for("portfolio_new"))

    form = PortfolioForm(obj=portfolio)
    if form.validate_on_submit():
        portfolio.title = form.title.data
        portfolio.description = form.description.data
        db.session.commit()
        flash("Portfolio updated.", "success")
        return redirect(url_for("profile", username=current_user.username))

    return render_template("portfolio_form.html", form=form, mode="edit")


@login_required
def holding_new():
    portfolio = current_user.portfolio
    if portfolio is None:
        flash("Create your portfolio first.", "error")
        return redirect(url_for("portfolio_new"))

    form = HoldingForm()
    if form.validate_on_submit():
        holding = Holding(
            portfolio=portfolio,
            ticker=form.ticker.data,
            shares=form.shares.data,
            buy_price=form.buy_price.data,
            buy_date=form.buy_date.data,
        )
        db.session.add(holding)
        db.session.commit()
        flash(f"Added {holding.ticker} to your portfolio.", "success")
        return redirect(url_for("profile", username=current_user.username))

    return render_template("holding_form.html", form=form)


@login_required
def holding_delete(holding_id):
    holding = db.session.get(Holding, holding_id)
    if holding is None:
        abort(404)
    if holding.portfolio.user_id != current_user.id:
        abort(403)

    ticker = holding.ticker
    db.session.delete(holding)
    db.session.commit()
    flash(f"Removed {ticker} from your portfolio.", "success")
    return redirect(url_for("profile", username=current_user.username))


def register(app):
    app.add_url_rule("/portfolio/new", view_func=portfolio_new, methods=["GET", "POST"])
    app.add_url_rule(
        "/portfolio/edit", view_func=portfolio_edit, methods=["GET", "POST"]
    )
    app.add_url_rule(
        "/portfolio/holdings/new", view_func=holding_new, methods=["GET", "POST"]
    )
    app.add_url_rule(
        "/holding/<int:holding_id>/delete", view_func=holding_delete, methods=["POST"]
    )
