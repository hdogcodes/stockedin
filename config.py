"""Application configuration."""

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    # Falls back to a dev value so the app still runs without a .env file.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    # Relative path is resolved against Flask's instance/ folder because the app
    # is created with instance_relative_config=True.
    SQLALCHEMY_DATABASE_URI = "sqlite:///portfolio.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # How long a fetched stock quote stays fresh before we hit the API again.
    PRICE_CACHE_TTL_SECONDS = 300
