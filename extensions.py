"""Uninitialized extension objects.

These live apart from app.py so models and route modules can import them
without circular imports. app.py calls init_app() on each.
"""

from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message_category = "error"
