"""Signup, login and logout views."""

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from extensions import db
from forms import LoginForm, ProfileForm, SignupForm
from images import AUTH_HERO_IMAGE
from login_throttle import clear, is_locked_out, record_failure
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
        if is_locked_out(identifier, request.remote_addr):
            flash("Too many failed attempts. Try again in a minute.", "error")
            return render_template("login.html", form=form, auth_hero_image=AUTH_HERO_IMAGE)

        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier.lower())
        ).first()
        if user is None or not user.check_password(form.password.data):
            record_failure(identifier, request.remote_addr)
            flash("Incorrect username or password.", "error")
        else:
            clear(identifier, request.remote_addr)
            login_user(user)
            # Only follow ?next= when it is a genuine local path — reject
            # absolute URLs and protocol-relative "//evil.com" alike.
            next_page = request.args.get("next")
            if not next_page or not next_page.startswith("/") or next_page.startswith("//"):
                next_page = url_for("feed")
            return redirect(next_page)

    return render_template("login.html", form=form, auth_hero_image=AUTH_HERO_IMAGE)


@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@login_required
def profile_edit():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.bio = form.bio.data or None
        current_user.university = form.university.data or None
        current_user.degree = form.degree.data or None
        current_user.grad_year = form.grad_year.data or None
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("profile", username=current_user.username))

    return render_template("profile_form.html", form=form)


def register(app):
    app.add_url_rule("/signup", view_func=signup, methods=["GET", "POST"])
    app.add_url_rule("/login", view_func=login, methods=["GET", "POST"])
    app.add_url_rule("/logout", view_func=logout)
    app.add_url_rule("/profile/edit", view_func=profile_edit, methods=["GET", "POST"])
