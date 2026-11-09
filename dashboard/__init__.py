"""Portflow coach dashboard: a local Flask web app (see docs/architectuur.md)."""

from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, abort, request

from . import db, routes

DEFAULT_DATABASE = Path(__file__).resolve().parent.parent / "data" / "dashboard.sqlite3"
LOCAL_HOSTS = {"127.0.0.1", "localhost"}


def create_app(database_path: Path | str | None = None) -> Flask:
    app = Flask(__name__)
    app.config["DATABASE"] = str(database_path or DEFAULT_DATABASE)

    db.init_app(app)
    app.add_url_rule("/favicon.ico", "favicon",
                     lambda: app.send_static_file("favicon.svg"))
    app.register_blueprint(routes.bp)

    @app.before_request
    def only_local_requests():
        # The app only listens on 127.0.0.1. These checks also stop other
        # websites from using the browser to reach it (DNS rebinding, CSRF).
        if request.host.rsplit(":", 1)[0] not in LOCAL_HOSTS:
            abort(400)
        origin = request.headers.get("Origin")
        if request.method == "POST" and origin and urlparse(origin).netloc != request.host:
            abort(403)

    return app
