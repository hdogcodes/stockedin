"""App factory and entrypoint. Run with `python app.py`."""

from flask import Flask

import routes_auth
import routes_portfolio
import routes_social
from config import Config
from extensions import db, login_manager


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    routes_auth.register(app)
    routes_portfolio.register(app)
    routes_social.register(app)

    return app


app = create_app()

if __name__ == "__main__":
    # use_reloader=False: Werkzeug's file-watcher reloader restarts itself by
    # exiting with a special code, which VS Code's debugger (debugpy)
    # surfaces as an unhandled "SystemExit: 3" instead of handling silently.
    # debug=True is kept for the interactive error pages and template
    # auto-reload; just restart the debugger to pick up .py changes.
    app.run(debug=True, use_reloader=False)

