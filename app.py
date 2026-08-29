"""App factory and entrypoint. Run with `python app.py`."""

from flask import Flask
from flask_login import current_user

import routes_auth
import routes_discover
import routes_groups
import routes_messages
import routes_news
import routes_portfolio
import routes_predictions
import routes_social
from config import Config
from extensions import csrf, db, login_manager


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    routes_auth.register(app)
    routes_portfolio.register(app)
    routes_social.register(app)
    routes_news.register(app)
    routes_messages.register(app)
    routes_discover.register(app)
    routes_groups.register(app)
    routes_predictions.register(app)

    @app.context_processor
    def inject_unread_message_count():
        if current_user.is_authenticated:
            return {"unread_message_count": current_user.unread_message_count}
        return {"unread_message_count": 0}

    return app


app = create_app()

if __name__ == "__main__":
    # use_reloader=False: Werkzeug's file-watcher reloader restarts itself by
    # exiting with a special code, which VS Code's debugger (debugpy)
    # surfaces as an unhandled "SystemExit: 3" instead of handling silently.
    # debug=True is kept for the interactive error pages and template
    # auto-reload; just restart the debugger to pick up .py changes.
    app.run(debug=True, use_reloader=False)

