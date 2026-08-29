"""In-memory brute-force throttle for the login form.

No new dependency (no Flask-Limiter) — same lightweight in-process cache
pattern already used in prices.py. Tracks failed attempts per (identifier,
IP) pair; a single-process dev server is exactly the deployment shape this
app targets, so this is proportionate, not a stand-in for a real rate
limiter behind a load balancer.
"""

import time

MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 60

# (identifier, ip) -> (failure_count, first_failure_at)
_attempts = {}


def _key(identifier, ip):
    return (identifier.strip().lower(), ip)


def is_locked_out(identifier, ip):
    entry = _attempts.get(_key(identifier, ip))
    if entry is None:
        return False
    count, first_at = entry
    if count < MAX_ATTEMPTS:
        return False
    if time.time() - first_at > LOCKOUT_SECONDS:
        del _attempts[_key(identifier, ip)]
        return False
    return True


def record_failure(identifier, ip):
    key = _key(identifier, ip)
    count, first_at = _attempts.get(key, (0, time.time()))
    _attempts[key] = (count + 1, first_at)


def clear(identifier, ip):
    _attempts.pop(_key(identifier, ip), None)
