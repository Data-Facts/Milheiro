"""Application factory for the Milheiro API."""
from __future__ import annotations

from flask import Flask

from .routes import api_blueprint


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.register_blueprint(api_blueprint)
    return app


__all__ = ["create_app"]
