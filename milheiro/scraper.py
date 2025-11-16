"""Scraper utilities for collecting award seats from seats.aero."""
from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any, Dict, Iterable, List, Mapping, Optional

import requests
from bs4 import BeautifulSoup

BASE_URL = os.getenv("SEATS_AERO_URL", "https://seats.aero/search")
DEFAULT_PARAMS: Dict[str, Any] = {
    "min_seats": 1,
    "applicable_cabin": "any",
    "additional_days": "true",
    "additional_days_num": 14,
    "max_fees": 40000,
    "disable_live_filtering": "false",
}
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)
HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "30"))
COLUMN_NAMES = [
    "Data",
    "Ultima_Visualizacao",
    "Programa",
    "Origem",
    "Destino",
    "Economica",
    "Premium",
    "Executiva",
    "PrimeiraClasse",
]

_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": USER_AGENT})


@dataclass(frozen=True)
class SearchQuery:
    """Represents the scraper query parameters."""

    date: str
    origin: str
    destination: str

    def as_params(self, defaults: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        """Return the query as request parameters."""

        params = dict(defaults or DEFAULT_PARAMS)
        params.update(
            {
                "date": self.date,
                "origins": _normalize_airport(self.origin),
                "destinations": _normalize_airport(self.destination),
            }
        )
        return params


def _normalize_airport(value: str) -> str:
    value = value.strip().upper()
    if len(value) != 3:
        raise ValueError("Códigos IATA devem possuir três letras.")
    return value


def _extract_table_rows(html: str) -> List[List[str]]:
    soup = BeautifulSoup(html, "html.parser")
    table_body = soup.select_one("table#DataTables_Table_0 tbody")
    if not table_body:
        return []

    rows: List[List[str]] = []
    for tr in table_body.select("tr"):
        columns = tr.select("td")
        if not columns:
            continue
        values: List[str] = []
        for td in columns:
            span = td.find("span")
            if span:
                text = span.get_text(strip=True)
                tooltip = span.get("data-bs-original-title")
                if tooltip:
                    values.append(f"{text} | tooltip: {tooltip}")
                else:
                    values.append(text)
            else:
                values.append(td.get_text(strip=True))
        rows.append(values)
    return rows


def _rows_to_records(rows: Iterable[Iterable[str]]) -> List[Dict[str, str]]:
    records: List[Dict[str, str]] = []
    seen: set[tuple[str, ...]] = set()

    for row in rows:
        trimmed = list(row)[: len(COLUMN_NAMES)]
        if not trimmed:
            continue
        fingerprint = tuple(trimmed)
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        record = {column: value for column, value in zip(COLUMN_NAMES, trimmed)}
        records.append(record)

    return records


def _fetch_html(
    query: SearchQuery,
    *,
    base_url: str,
    timeout: int,
    default_params: Mapping[str, Any],
) -> str:
    response = _SESSION.get(
        base_url,
        params=query.as_params(defaults=default_params),
        timeout=timeout,
    )
    response.raise_for_status()
    return response.text


def search_availability(
    query: SearchQuery,
    *,
    base_url: str | None = None,
    timeout: int | None = None,
    default_params: Optional[Mapping[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Return seat availability for the provided query."""

    html = _fetch_html(
        query,
        base_url=base_url or BASE_URL,
        timeout=timeout or HTTP_TIMEOUT,
        default_params=default_params or DEFAULT_PARAMS,
    )
    rows = _extract_table_rows(html)
    return _rows_to_records(rows)


__all__ = ["SearchQuery", "search_availability", "DEFAULT_PARAMS", "BASE_URL", "HTTP_TIMEOUT"]
