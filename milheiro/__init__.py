"""Application factory for the Milheiro API."""
from __future__ import annotations

from flask import Flask

from .config import Config
from .errors import register_error_handlers
from .routes import api_blueprint


def create_app(config_object: type[Config] | None = None) -> Flask:
    """Create and configure the Flask application."""

    app = Flask(__name__)
    app.config.from_object(config_object or Config)

    register_error_handlers(app)
    app.register_blueprint(api_blueprint)
    return app


__all__ = ["create_app", "Config"]
