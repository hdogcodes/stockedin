"""Finance news page."""

from datetime import datetime

from flask import render_template
from flask_login import login_required

from news import get_market_news


@login_required
def news():
    articles = get_market_news()
    for article in articles:
        ts = article.get("datetime")
        article["published"] = (
            datetime.utcfromtimestamp(ts).strftime("%b %d, %Y %H:%M") if ts else ""
        )
    return render_template("news.html", articles=articles)


def register(app):
    app.add_url_rule("/news", view_func=news)
