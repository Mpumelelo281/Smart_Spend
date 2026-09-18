"""Checkers product search adapter.

Unlike SerpApi (a licensed third-party API — see serpapi_google_shopping.py),
Checkers has no documented public shopping API, so this adapter talks to a
*configurable* JSON search endpoint (CHECKERS_API_BASE_URL) instead of a
hard-coded scrape target — the same "don't hard-code a source, configure
it" principle as every other adapter setting in this project. It stays
fully inert (is_configured() False, never called by live_search.py) until
that setting is supplied, exactly like an unset SERPAPI_KEY.

IMPORTANT: the field mapping in `_normalize` below is a best-effort guess
at a typical retailer search-API response shape (id/name/price/category).
Before pointing CHECKERS_API_BASE_URL at a real endpoint, verify the
endpoint's actual response schema and adjust `_normalize` to match — never
assume it's correct untested, per this project's "don't fabricate" rule
(see geo.py, serpapi_google_shopping.py for the same principle applied
elsewhere). Confirm the endpoint's terms of use permit this kind of
automated querying before enabling in any deployed environment.
"""

import logging

import pybreaker
import requests
from django.conf import settings

from .base import AdapterUnavailable, NormalizedListing, RetailerAdapter

logger = logging.getLogger(__name__)

_breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=60)


class CheckersAdapter(RetailerAdapter):
    name = "checkers"
    _timeout_seconds = 8

    def is_configured(self) -> bool:
        return bool(settings.CHECKERS_API_BASE_URL)

    def search(self, query: str) -> list[NormalizedListing]:
        if not self.is_configured():
            raise AdapterUnavailable("CHECKERS_API_BASE_URL is not set.")

        try:
            data = self._call_api(query)
        except pybreaker.CircuitBreakerError as exc:
            raise AdapterUnavailable("Circuit open: Checkers has failed repeatedly recently.") from exc
        except requests.RequestException as exc:
            raise AdapterUnavailable(f"Checkers request failed: {exc}") from exc

        return [listing for raw in data.get("results", []) if (listing := self._normalize(raw))]

    @_breaker
    def _call_api(self, query: str) -> dict:
        headers = {}
        if settings.CHECKERS_API_KEY:
            headers["Authorization"] = f"Bearer {settings.CHECKERS_API_KEY}"

        response = requests.get(
            settings.CHECKERS_API_BASE_URL,
            params={"q": query},
            headers=headers,
            timeout=self._timeout_seconds,
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _normalize(raw: dict) -> NormalizedListing | None:
        name = raw.get("name")
        price = raw.get("price")
        if not name or price is None:
            return None

        return NormalizedListing(
            product_name=name,
            retailer_name="Checkers",
            price=float(price),
            delivery_cost=float(raw.get("delivery_cost") or 0.0),
            category=raw.get("category"),
            retailer_base_url="https://www.checkers.co.za",
        )
