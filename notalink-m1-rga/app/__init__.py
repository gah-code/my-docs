from __future__ import annotations
from flask import Flask
from .routes import ui

def create_app() -> Flask:
    app = Flask(__name__)
    try:
        from notalink.settings import get_settings
        app.config["SECRET_KEY"] = get_settings().SECRET_KEY
    except Exception:
        app.config["SECRET_KEY"] = "dev"
    app.register_blueprint(ui)
    return app
