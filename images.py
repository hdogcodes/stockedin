"""Curated real photo URLs (Unsplash CDN) used as page/profile background
imagery, in place of flat CSS gradients."""

import hashlib

AUTH_HERO_IMAGE = (
    "https://images.unsplash.com/photo-1518186285589-2f7649de83e0"
    "?auto=format&fit=crop&w=1600&q=70"
)

# A small rotating set of finance/city/chart photos for profile cover banners.
COVER_IMAGES = [
    "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1200&q=60",
    "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=1200&q=60",
    "https://images.unsplash.com/photo-1590479773265-7464e5d48118?auto=format&fit=crop&w=1200&q=60",
    "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?auto=format&fit=crop&w=1200&q=60",
    "https://images.unsplash.com/photo-1560221328-12fe60f83ab8?auto=format&fit=crop&w=1200&q=60",
    "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=1200&q=60",
]


def cover_image_for(username):
    """Deterministic per-user pick so a profile's cover photo stays stable
    across visits instead of changing every page load.

    Uses md5 rather than the builtin hash() — Python randomizes str hash()
    per process (PYTHONHASHSEED), which would reshuffle everyone's cover
    photo on every server restart.
    """
    digest = hashlib.md5(username.encode()).hexdigest()
    return COVER_IMAGES[int(digest, 16) % len(COVER_IMAGES)]
