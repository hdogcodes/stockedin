"""Feed, profile, follow/unfollow, and AJAX like/comment views."""

from flask import abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from extensions import db
from forms import CommentForm
from models import Comment, Follow, Like, Portfolio, User
from prices import attach_stats
from snapshots import get_chart_series, record_snapshot


@login_required
def feed():
    followed_ids = [f.followed_id for f in current_user.following]
    portfolios = (
        Portfolio.query.filter(Portfolio.user_id.in_(followed_ids))
        .order_by(Portfolio.created_at.desc())
        .all()
        if followed_ids
        else []
    )
    attach_stats(portfolios)
    comment_form = CommentForm()
    users = (
        User.query.filter(User.id != current_user.id)
        .order_by(User.username)
        .all()
    )
    for user in users:
        user.held_tickers = (
            sorted({h.ticker for h in user.portfolio.holdings}) if user.portfolio else []
        )
    return render_template(
        "feed.html", portfolios=portfolios, comment_form=comment_form, users=users
    )


@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    portfolios = [user.portfolio] if user.portfolio else []
    attach_stats(portfolios)
    comment_form = CommentForm()

    chart_series = []
    if user.portfolio is not None:
        total_value = portfolios[0].stats.get("total_value")
        record_snapshot(user.portfolio, total_value)
        chart_series = get_chart_series(user.portfolio)

    return render_template(
        "profile.html",
        profile_user=user,
        portfolios=portfolios,
        comment_form=comment_form,
        chart_series=chart_series,
    )


def _redirect_back(fallback_endpoint, **fallback_values):
    # Keeps the user on whatever page they clicked Follow/Unfollow from
    # (e.g. the feed sidebar) instead of always jumping to a profile page.
    if request.referrer:
        return redirect(request.referrer)
    return redirect(url_for(fallback_endpoint, **fallback_values))


@login_required
def follow(username):
    target = User.query.filter_by(username=username).first_or_404()
    if target.id == current_user.id:
        flash("You can't follow yourself.", "error")
        return _redirect_back("profile", username=username)

    already = Follow.query.filter_by(
        follower_id=current_user.id, followed_id=target.id
    ).first()
    if not already:
        db.session.add(Follow(follower_id=current_user.id, followed_id=target.id))
        db.session.commit()

    return _redirect_back("profile", username=username)


@login_required
def unfollow(username):
    target = User.query.filter_by(username=username).first_or_404()
    Follow.query.filter_by(
        follower_id=current_user.id, followed_id=target.id
    ).delete()
    db.session.commit()
    return _redirect_back("profile", username=username)


@login_required
def like_portfolio(portfolio_id):
    portfolio = db.session.get(Portfolio, portfolio_id)
    if portfolio is None:
        abort(404)

    existing = Like.query.filter_by(
        user_id=current_user.id, portfolio_id=portfolio.id
    ).first()
    if existing:
        db.session.delete(existing)
        liked = False
    else:
        db.session.add(Like(user_id=current_user.id, portfolio_id=portfolio.id))
        liked = True
    db.session.commit()

    like_count = Like.query.filter_by(portfolio_id=portfolio.id).count()
    return jsonify({"liked": liked, "like_count": like_count})


@login_required
def comment_portfolio(portfolio_id):
    portfolio = db.session.get(Portfolio, portfolio_id)
    if portfolio is None:
        abort(404)

    form = CommentForm()
    if not form.validate_on_submit():
        errors = [msg for field_errors in form.errors.values() for msg in field_errors]
        return jsonify({"error": errors[0] if errors else "Invalid comment."}), 400

    comment = Comment(user_id=current_user.id, portfolio_id=portfolio.id, body=form.body.data)
    db.session.add(comment)
    db.session.commit()

    return jsonify(
        {
            "username": current_user.username,
            "body": comment.body,
            "created_at": comment.created_at.strftime("%b %d, %Y %H:%M"),
        }
    )


def register(app):
    app.add_url_rule("/", view_func=feed)
    app.add_url_rule("/user/<username>", view_func=profile)
    app.add_url_rule("/follow/<username>", view_func=follow, methods=["POST"])
    app.add_url_rule("/unfollow/<username>", view_func=unfollow, methods=["POST"])
    app.add_url_rule(
        "/portfolio/<int:portfolio_id>/like", view_func=like_portfolio, methods=["POST"]
    )
    app.add_url_rule(
        "/portfolio/<int:portfolio_id>/comment",
        view_func=comment_portfolio,
        methods=["POST"],
    )
