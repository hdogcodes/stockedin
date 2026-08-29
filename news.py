"""Finance news via the Finnhub API, with a small in-memory cache.

Reuses FINNHUB_API_KEY (the same key used for stock quotes in prices.py) —
Finnhub's free tier also includes a market-news endpoint, so no separate
signup is needed. Like prices.py, this never raises: a network hiccup just
means an empty news list rather than a broken page.
"""

import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")
FINNHUB_NEWS_URL = "https://finnhub.io/api/v1/news"
REQUEST_TIMEOUT_SECONDS = 4

_cache = {"articles": None, "fetched_at": 0}
CACHE_TTL_SECONDS = 600


def _fetch():
    if not FINNHUB_API_KEY:
        return []
    try:
        response = requests.get(
            FINNHUB_NEWS_URL,
            params={"category": "general", "token": FINNHUB_API_KEY},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
    except Exception:
        return []

    if not isinstance(data, list):
        return []

    articles = []
    for item in data:
        headline = item.get("headline")
        url = item.get("url")
        image = item.get("image")
        # Skip anything without an image — this page is meant to be visual,
        # and Finnhub occasionally returns entries with a blank image field.
        if not headline or not url or not image:
            continue
        articles.append(
            {
                "id": item.get("id"),
                "headline": headline,
                "summary": item.get("summary") or "",
                "image": image,
                "source": item.get("source") or "",
                "url": url,
                "datetime": item.get("datetime"),
            }
        )
    return articles


def get_market_news():
    """Return a list of finance news articles (with images), or [] on failure."""
    if _cache["articles"] is not None and time.time() - _cache["fetched_at"] < CACHE_TTL_SECONDS:
        return _cache["articles"]

    articles = _fetch()
    if articles:
        _cache["articles"] = articles
        _cache["fetched_at"] = time.time()
        return articles

    # Fetch failed — serve stale cache if we have one rather than an empty page.
    return _cache["articles"] or []
