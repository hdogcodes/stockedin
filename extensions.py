"""Uninitialized extension objects.

These live apart from app.py so models and route modules can import them
without circular imports. app.py calls init_app() on each.
"""

from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message_category = "error"

# Global CSRF protection for every state-changing request, not just routes
# that happen to render a FlaskForm. Without this, plain POST forms (like
# follow/unfollow and holding-delete) had zero CSRF defense — Flask-WTF only
# auto-checks views that call form.validate_on_submit().
csrf = CSRFProtect()
