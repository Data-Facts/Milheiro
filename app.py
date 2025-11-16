"""Flask microservice that exposes the Milheiro scraping endpoints."""
from __future__ import annotations

import os
from http import HTTPStatus
from typing import Any, Dict

from flask import Flask, jsonify, request
from requests import HTTPError, Timeout

from milheiro.scraper import (
    BASE_URL,
    DEFAULT_PARAMS,
    HTTP_TIMEOUT,
    SearchQuery,
    search_availability,
)


def _scraper_overrides() -> Dict[str, Any]:
    """Load scraper overrides defined via environment variables."""

    mapping = {
        "min_seats": ("SCRAPER_MIN_SEATS", int),
        "applicable_cabin": ("SCRAPER_APPLICABLE_CABIN", str),
        "additional_days": ("SCRAPER_ADDITIONAL_DAYS", str),
        "additional_days_num": ("SCRAPER_ADDITIONAL_DAYS_NUM", int),
        "max_fees": ("SCRAPER_MAX_FEES", int),
        "disable_live_filtering": ("SCRAPER_DISABLE_LIVE_FILTERING", str),
    }
    overrides: Dict[str, Any] = {}
    for key, (env_name, caster) in mapping.items():
        value = os.getenv(env_name)
        if value is None:
            continue
        overrides[key] = caster(value)
    return overrides


app = Flask(__name__)
app.config.from_mapping(
    {
        "JSON_SORT_KEYS": False,
        "SEATS_AERO_URL": os.getenv("SEATS_AERO_URL", BASE_URL),
        "HTTP_TIMEOUT": int(os.getenv("HTTP_TIMEOUT", str(HTTP_TIMEOUT))),
        "SCRAPER_DEFAULTS": {**DEFAULT_PARAMS, **_scraper_overrides()},
    }
)


def _parse_query_params() -> SearchQuery:
    origin = request.args.get("origin")
    destination = request.args.get("destination")
    date = request.args.get("date")

    missing = [
        name
        for name, value in (("origin", origin), ("destination", destination), ("date", date))
        if not value
    ]
    if missing:
        raise ValueError(f"Parâmetros obrigatórios ausentes: {', '.join(missing)}")

    return SearchQuery(date=date, origin=origin, destination=destination)


@app.route("/", methods=["GET"])
def index() -> Any:
    """Return metadata about the service."""

    return (
        jsonify(
            {
                "service": "Milheiro API",
                "description": "Raspador de disponibilidade de assentos do seats.aero sem Selenium.",
                "endpoints": {
                    "health": "/healthz",
                    "scraper": "/scraper?origin=GRU&destination=MIA&date=2024-07-01",
                },
            }
        ),
        HTTPStatus.OK,
    )


@app.route("/healthz", methods=["GET"])
def healthcheck() -> Any:
    """Health-check endpoint consumed by Render."""

    return jsonify({"status": "ok"}), HTTPStatus.OK


@app.route("/scraper", methods=["GET"])
def scraper() -> Any:
    """Return scraped availability for the requested route and date."""

    try:
        query = _parse_query_params()
    except ValueError as exc:
        return jsonify({"error": str(exc)}), HTTPStatus.BAD_REQUEST

    config = app.config
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
