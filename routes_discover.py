"""Explore (trending / top / tag filters / new) and student-investor
discovery — the "find strategies and people worth following" surface."""

from flask import render_template, request
from flask_login import current_user, login_required

from models import Portfolio, User
from prices import attach_stats

EXPLORE_TABS = [
    ("trending", "Trending"),
    ("top", "Top Performing"),
    ("students", "Student Investors"),
    ("growth", "Growth"),
    ("dividend", "Dividend"),
    ("ai", "AI"),
    ("low-risk", "Low Risk"),
    ("new", "New Portfolios"),
]

TAB_TAGS = {
    "growth": "Growth",
    "dividend": "Dividend",
    "ai": "AI",
    "low-risk": "Low Risk",
}


def _portfolios_for_tab(tab):
    query = Portfolio.query.join(User, Portfolio.user_id == User.id)

    if tab == "students":
        portfolios = query.filter(User.university.isnot(None)).all()
    elif tab in TAB_TAGS:
        tag = TAB_TAGS[tab]
        portfolios = [p for p in Portfolio.query.all() if tag in p.tag_list]
    elif tab == "new":
        portfolios = Portfolio.query.order_by(Portfolio.created_at.desc()).limit(24).all()
    else:
        portfolios = Portfolio.query.all()

    attach_stats(portfolios)

    if tab == "top":
        portfolios = sorted(
            (p for p in portfolios if p.stats.get("total_gain_loss_pct") is not None),
            key=lambda p: p.stats["total_gain_loss_pct"],
            reverse=True,
        )
    elif tab == "trending":
        portfolios = sorted(
            portfolios, key=lambda p: (p.like_count + len(p.comments)), reverse=True
        )
    elif tab != "new":
        portfolios = sorted(portfolios, key=lambda p: p.created_at, reverse=True)

    return portfolios[:24]


@login_required
def explore():
    tab = request.args.get("tab", "trending")
    if tab not in dict(EXPLORE_TABS):
        tab = "trending"

    portfolios = _portfolios_for_tab(tab)

    return render_template(
        "explore.html", portfolios=portfolios, tabs=EXPLORE_TABS, active_tab=tab
    )


@login_required
def student_investors():
    students = (
        User.query.filter(User.university.isnot(None))
        .filter(User.id != current_user.id)
        .order_by(User.university, User.username)
        .all()
    )
    same_university = (
        [u for u in students if u.university == current_user.university]
        if current_user.university
        else []
    )
    return render_template(
        "student_investors.html", students=students, same_university=same_university
    )


def register(app):
    app.add_url_rule("/explore", view_func=explore)
    app.add_url_rule("/students", view_func=student_investors)
