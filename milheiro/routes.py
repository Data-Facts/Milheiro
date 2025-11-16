"""HTTP routes for the Milheiro API."""
from __future__ import annotations

from http import HTTPStatus
from typing import Any, Dict

from flask import Blueprint, current_app, jsonify, request
from requests import HTTPError, Timeout

from .scraper import SearchQuery, search_availability

api_blueprint = Blueprint("milheiro", __name__)


@api_blueprint.route("/", methods=["GET"])
def index() -> Any:
    """Return metadata about the service and example usage."""

    return (
        jsonify(
            {
                "service": "Milheiro API",
                "documentation": "Consulte o README para instruções de uso.",
                "endpoints": {
                    "healthcheck": "/healthz",
                    "scraper": "/scraper?origin=GRU&destination=MIA&date=2024-07-01",
                },
            }
        ),
        HTTPStatus.OK,
    )


@api_blueprint.route("/healthz", methods=["GET"])
def healthcheck() -> Any:
    """Basic health-check endpoint used by Render."""

    return jsonify({"status": "ok"}), HTTPStatus.OK


def _parse_query_params() -> SearchQuery:
    """Validate and convert the incoming query parameters."""

    origin = request.args.get("origin")
    destination = request.args.get("destination")
    date = request.args.get("date")

    pairs = (("origin", origin), ("destination", destination), ("date", date))
    missing = [name for name, value in pairs if not value]
    if missing:
        raise ValueError(f"Parâmetros obrigatórios ausentes: {', '.join(missing)}")

    return SearchQuery(date=date, origin=origin, destination=destination)


@api_blueprint.route("/scraper", methods=["GET"])
def scraper() -> Any:
    """Return scraped award availability for the given query parameters."""

    try:
        query = _parse_query_params()
    except ValueError as exc:
        return jsonify({"error": str(exc)}), HTTPStatus.BAD_REQUEST

    config = current_app.config
    base_url: str = config["SEATS_AERO_URL"]
    timeout: int = config["HTTP_TIMEOUT"]
    defaults: Dict[str, Any] = config["SCRAPER_DEFAULTS"]

    try:
        records = search_availability(
            query,
            base_url=base_url,
            timeout=timeout,
            default_params=defaults,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), HTTPStatus.BAD_REQUEST
    except Timeout:
        return jsonify({"error": "Tempo limite excedido ao consultar o seats.aero."}), HTTPStatus.GATEWAY_TIMEOUT
    except HTTPError as exc:
        status_code = exc.response.status_code if exc.response else HTTPStatus.BAD_GATEWAY
        return jsonify({"error": f"Falha ao acessar seats.aero: {status_code}"}), status_code

    if not records:
        return jsonify({"mensagem": "Nenhum dado encontrado."}), HTTPStatus.OK

    return jsonify(records), HTTPStatus.OK


__all__ = ["api_blueprint"]
