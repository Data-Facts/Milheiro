"""Reusable error handlers for the Milheiro API."""
from __future__ import annotations

from http import HTTPStatus
from typing import Any, Tuple

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException


def register_error_handlers(app: Flask) -> None:
    """Attach JSON error handlers to the Flask app."""

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException) -> Tuple[Any, int]:
        response = getattr(exc, "description", str(exc))
        return jsonify({"error": response}), exc.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc: Exception) -> Tuple[Any, int]:  # pragma: no cover - defensive
        app.logger.exception("Unhandled exception", exc_info=exc)
        return jsonify({"error": "Erro interno inesperado."}), HTTPStatus.INTERNAL_SERVER_ERROR


__all__ = ["register_error_handlers"]
