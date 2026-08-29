"""Live stock quotes via the Finnhub API, with a small in-memory cache.

Every lookup goes through get_quote(), which never raises: a bad ticker, a
network timeout, or an API hiccup all come back as None so a single bad
holding can't take down a whole page.

Finnhub (not yfinance) is used because it's an official, documented API with
a real key rather than an unofficial scraper of Yahoo's internal endpoints —
Yahoo has a habit of throttling/blocking yfinance, which showed up as slow
or malformed responses. Get a free key at https://finnhub.io/register and
set FINNHUB_API_KEY in .env (60 requests/min on the free tier, which this
app's caching stays well under).

Two things make this fast enough to call on every page render:
  - REQUEST_TIMEOUT_SECONDS bounds each HTTP call. Without it, the requests
    library waits indefinitely, so one unreachable/slow lookup can hang a
    page render for minutes instead of failing in a few seconds.
  - Failed lookups are cached too (briefly), so repeatedly loading a page
    with a bad/unreachable ticker doesn't retry the slow network call on
    every single request.
"""

import math
import os
import time
from concurrent.futures import ThreadPoolExecutor

import requests
from dotenv import load_dotenv

load_dotenv()

FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")
FINNHUB_QUOTE_URL = "https://finnhub.io/api/v1/quote"
FINNHUB_SEARCH_URL = "https://finnhub.io/api/v1/search"

# ticker -> (quote_dict_or_None, fetched_at_epoch)
_cache = {}

# lowercased query -> (results_list, fetched_at_epoch)
_search_cache = {}

CACHE_TTL_SECONDS = 300
FAILURE_CACHE_TTL_SECONDS = 60
SEARCH_CACHE_TTL_SECONDS = 300
REQUEST_TIMEOUT_SECONDS = 4
SEARCH_RESULT_LIMIT = 8


def _clean(value):
    """Treat missing/zero/negative numbers as "no data" (Finnhub returns all
    zeros — c=0, pc=0, etc. — for an unknown symbol instead of an error)."""
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(value) or value <= 0:
        return None
    return value


def _to_float(value):
    """Like _clean but keeps zero/negative — for fields like % change where
    a down day is a legitimate, meaningful negative number, not "no data"."""
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(value) else value


def _fetch(ticker):
    """Actually hit the network. Never raises — returns a quote dict or None."""
    if not FINNHUB_API_KEY:
        return None
    try:
        response = requests.get(
            FINNHUB_QUOTE_URL,
            params={"symbol": ticker, "token": FINNHUB_API_KEY},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
    except Exception:
        return None

    price = _clean(data.get("c"))
    if price is None:
        return None

    prev_close = _clean(data.get("pc"))
    day_change_pct = _to_float(data.get("dp"))
    if day_change_pct is None and prev_close:
        day_change_pct = (price - prev_close) / prev_close * 100

    return {
        "price": price,
        "prev_close": prev_close,
        "day_change_pct": day_change_pct,
    }


def get_quote(ticker):
    """Return {price, prev_close, day_change_pct} for a ticker, or None.

    None means "we could not get a price" — unknown ticker, delisted stock,
    or the API being unreachable. Callers must handle it.
    """
    if not ticker:
        return None
    ticker = ticker.strip().upper()

    cached = _cache.get(ticker)
    if cached is not None:
        quote, fetched_at, ok = cached
        ttl = CACHE_TTL_SECONDS if ok else FAILURE_CACHE_TTL_SECONDS
        if time.time() - fetched_at < ttl:
            return quote

    quote = _fetch(ticker)
    _cache[ticker] = (quote, time.time(), quote is not None)
    return quote


def prefetch_quotes(tickers):
    """Warm the cache for several tickers concurrently.

    Fetching N uncached tickers one at a time means N sequential network
    round-trips (each up to REQUEST_TIMEOUT_SECONDS). Doing it with a small
    thread pool first means a page with several distinct tickers pays for
    the slowest single lookup instead of the sum of all of them.
    """
    tickers = {t.strip().upper() for t in tickers if t}
    now = time.time()

    def is_fresh(ticker):
        cached = _cache.get(ticker)
        if cached is None:
            return False
        _, fetched_at, ok = cached
        ttl = CACHE_TTL_SECONDS if ok else FAILURE_CACHE_TTL_SECONDS
        return now - fetched_at < ttl

    stale = [t for t in tickers if not is_fresh(t)]
    if not stale:
        return

    with ThreadPoolExecutor(max_workers=min(8, len(stale))) as pool:
        results = pool.map(_fetch, stale)
        for ticker, quote in zip(stale, results):
            _cache[ticker] = (quote, time.time(), quote is not None)


WATCHLIST_TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "SPY"]


def get_watchlist_quotes():
    """Quotes for a fixed set of well-known tickers, for the ticker-tape
    strip. Reuses the same 5-minute cache as everything else, so this adds
    no real request volume beyond the first render after a cache miss."""
    prefetch_quotes(WATCHLIST_TICKERS)
    quotes = []
    for ticker in WATCHLIST_TICKERS:
        quote = get_quote(ticker)
        if quote is not None:
            quotes.append({"ticker": ticker, **quote})
    return quotes


def search_symbols(query):
    """Look up tickers by symbol OR company name, e.g. "amazon" -> AMZN.

    Powers the autocomplete on the add-holding form. Never raises — a bad
    query or unreachable API just yields an empty list, so the dropdown
    silently has no suggestions instead of erroring the page.
    """
    query = (query or "").strip()
    if not query or not FINNHUB_API_KEY:
        return []

    key = query.lower()
    cached = _search_cache.get(key)
    if cached is not None:
        results, fetched_at = cached
        if time.time() - fetched_at < SEARCH_CACHE_TTL_SECONDS:
            return results

    try:
        response = requests.get(
            FINNHUB_SEARCH_URL,
            params={"q": query, "token": FINNHUB_API_KEY},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
    except Exception:
        return _search_cache.get(key, ([], 0))[0]

    results = []
    seen = set()
    for item in data.get("result", []):
        symbol = item.get("symbol")
        description = item.get("description")
        if not symbol or not description or symbol in seen:
            continue
        # Skip non-tradeable derivatives (warrants, index entries, etc.) so
        # the dropdown stays focused on things you can actually hold shares of.
        if item.get("type") not in ("Common Stock", ""):
            continue
        seen.add(symbol)
        results.append({"symbol": symbol, "description": description})
        if len(results) >= SEARCH_RESULT_LIMIT:
            break

    _search_cache[key] = (results, time.time())
    return results


def ticker_exists(ticker):
    """True if we can get a live price for this ticker (used by form validation)."""
    return get_quote(ticker) is not None


def enrich_portfolio(portfolio):
    """Build per-holding and total figures for a portfolio.

    Returns a dict of display-ready numbers. Holdings whose price could not be
    fetched are included with available=False so the template can show a dash
    instead of breaking, and they are left out of the totals.
    """
    rows = []
    total_cost = 0.0
    total_value = 0.0
    has_unavailable = False

    for holding in portfolio.holdings:
        cost_basis = holding.cost_basis
        quote = get_quote(holding.ticker)

        if quote is None:
            has_unavailable = True
            rows.append(
                {
                    "holding": holding,
                    "available": False,
                    "cost_basis": cost_basis,
                    "current_price": None,
                    "current_value": None,
                    "gain_loss": None,
                    "gain_loss_pct": None,
                    "day_change_pct": None,
                }
            )
            continue

        current_value = holding.shares * quote["price"]
        gain_loss = current_value - cost_basis
        rows.append(
            {
                "holding": holding,
                "available": True,
                "cost_basis": cost_basis,
                "current_price": quote["price"],
                "current_value": current_value,
                "gain_loss": gain_loss,
                "gain_loss_pct": (gain_loss / cost_basis * 100) if cost_basis else None,
                "day_change_pct": quote["day_change_pct"],
            }
        )
        total_cost += cost_basis
        total_value += current_value

    total_gain_loss = total_value - total_cost
    return {
        "rows": rows,
        "total_cost": total_cost,
        "total_value": total_value,
        "total_gain_loss": total_gain_loss,
        "total_gain_loss_pct": (
            (total_gain_loss / total_cost * 100) if total_cost else None
        ),
        "has_unavailable": has_unavailable,
    }


def attach_stats(portfolios):
    """Attach a .stats dict to each portfolio for the templates to read.

    Price enrichment is wrapped so that an unexpected failure degrades to an
    empty stats block rather than erroring the whole feed. Tickers across all
    given portfolios are prefetched concurrently first so a feed showing
    several portfolios pays for one round of parallel lookups, not one
    lookup per holding in sequence.
    """
    all_tickers = [h.ticker for p in portfolios for h in p.holdings]
    try:
        prefetch_quotes(all_tickers)
    except Exception:
        pass  # enrich_portfolio below still falls back to "unavailable" per holding

    for portfolio in portfolios:
        try:
            portfolio.stats = enrich_portfolio(portfolio)
        except Exception:
            portfolio.stats = {
                "rows": [
                    {
                        "holding": h,
                        "available": False,
                        "cost_basis": h.cost_basis,
                        "current_price": None,
                        "current_value": None,
                        "gain_loss": None,
                        "gain_loss_pct": None,
                        "day_change_pct": None,
                    }
                    for h in portfolio.holdings
                ],
                "total_cost": sum(h.cost_basis for h in portfolio.holdings),
                "total_value": None,
                "total_gain_loss": None,
                "total_gain_loss_pct": None,
                "has_unavailable": True,
            }
    return portfolios
