"""Signup, login and logout views."""

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from extensions import db
from forms import LoginForm, SignupForm
from images import AUTH_HERO_IMAGE
from models import User


def signup():
    if current_user.is_authenticated:
        return redirect(url_for("feed"))

    form = SignupForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data.lower(),
            bio=form.bio.data or None,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Welcome! Start by creating your portfolio.", "success")
        return redirect(url_for("portfolio_new"))

    return render_template("signup.html", form=form, auth_hero_image=AUTH_HERO_IMAGE)


def login():
    if current_user.is_authenticated:
        return redirect(url_for("feed"))

    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.username.data.strip()
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier.lower())
        ).first()
        if user is None or not user.check_password(form.password.data):
            flash("Incorrect username or password.", "error")
        else:
            login_user(user)
            # Only follow ?next= when it is a local path, never an absolute URL.
            next_page = request.args.get("next")
            if not next_page or not next_page.startswith("/"):
                next_page = url_for("feed")
            return redirect(next_page)

    return render_template("login.html", form=form, auth_hero_image=AUTH_HERO_IMAGE)


@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


def register(app):
    app.add_url_rule("/signup", view_func=signup, methods=["GET", "POST"])
    app.add_url_rule("/login", view_func=login, methods=["GET", "POST"])
    app.add_url_rule("/logout", view_func=logout)
