"""Scraper utilities for collecting award seats from seats.aero."""
from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Dict, Iterable, List

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_URL = os.getenv("SEATS_AERO_URL", "https://seats.aero/search")
DEFAULT_PARAMS = {
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

_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": USER_AGENT})


@dataclass(frozen=True)
class SearchQuery:
    """Represents the scraper query parameters."""

    date: str
    origin: str
    destination: str

    def as_params(self) -> Dict[str, str]:
        """Return the query as request parameters."""
        params = DEFAULT_PARAMS.copy()
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
    df = pd.DataFrame(rows)
    if df.empty:
        return []
    df = df.iloc[:, :9]
    df = df.drop_duplicates()
    df.columns = [
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
    return df.to_dict(orient="records")


def _fetch_html(query: SearchQuery) -> str:
    response = _SESSION.get(BASE_URL, params=query.as_params(), timeout=HTTP_TIMEOUT)
    response.raise_for_status()
    return response.text


def search_availability(query: SearchQuery) -> List[Dict[str, str]]:
    """Return seat availability for the provided query."""
    html = _fetch_html(query)
    rows = _extract_table_rows(html)
    return _rows_to_records(rows)


__all__ = ["SearchQuery", "search_availability"]
