"""Application configuration for the Milheiro API."""
from __future__ import annotations

import os
from typing import Any, Dict


class Config:
    """Base configuration loaded by the Flask application factory."""

    JSON_SORT_KEYS = False
    SEATS_AERO_URL = os.getenv("SEATS_AERO_URL", "https://seats.aero/search")
    HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "30"))

    # Default scraping parameters that mimic the filters used on seats.aero.
    SCRAPER_DEFAULTS: Dict[str, Any] = {
        "min_seats": int(os.getenv("SCRAPER_MIN_SEATS", "1")),
        "applicable_cabin": os.getenv("SCRAPER_APPLICABLE_CABIN", "any"),
        "additional_days": os.getenv("SCRAPER_ADDITIONAL_DAYS", "true"),
        "additional_days_num": int(os.getenv("SCRAPER_ADDITIONAL_DAYS_NUM", "14")),
        "max_fees": int(os.getenv("SCRAPER_MAX_FEES", "40000")),
        "disable_live_filtering": os.getenv("SCRAPER_DISABLE_LIVE_FILTERING", "false"),
    }


__all__ = ["Config"]
