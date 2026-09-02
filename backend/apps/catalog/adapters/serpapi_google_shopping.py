"""Live product/price data via SerpApi's Google Shopping engine
(https://serpapi.com/google-shopping-api) — a licensed, ToS-compliant way
to get real Google Shopping results, rather than scraping a retailer's
site or Google's search results directly.

Circuit breaker (Rule 6): three consecutive failures trip it for 60
seconds, so a SerpApi outage degrades to "search runs on whatever's
already cached in PriceRecord" instead of every request hanging on a dead
upstream. `pybreaker`'s default in-memory storage is per-process — good
enough for a single Django process; a multi-worker deployment would want
its Redis-backed storage instead, sharing breaker state across workers.
"""

import logging
from urllib.parse import urlparse

import pybreaker
import requests
from django.conf import settings

from .base import AdapterUnavailable, NormalizedListing, RetailerAdapter

logger = logging.getLogger(__name__)

_breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=60)


class SerpApiGoogleShoppingAdapter(RetailerAdapter):
    name = "serpapi_google_shopping"
    _endpoint = "https://serpapi.com/search.json"
    _timeout_seconds = 8

    def is_configured(self) -> bool:
        return bool(settings.SERPAPI_KEY)

    def search(self, query: str) -> list[NormalizedListing]:
        if not self.is_configured():
            raise AdapterUnavailable("SERPAPI_KEY is not set.")

        try:
            data = self._call_serpapi(query)
        except pybreaker.CircuitBreakerError as exc:
            raise AdapterUnavailable("Circuit open: SerpApi has failed repeatedly recently.") from exc
        except requests.RequestException as exc:
            raise AdapterUnavailable(f"SerpApi request failed: {exc}") from exc

        return [listing for raw in data.get("shopping_results", []) if (listing := self._normalize(raw))]

    @_breaker
    def _call_serpapi(self, query: str) -> dict:
        response = requests.get(
            self._endpoint,
            params={
                "engine": "google_shopping",
                "q": query,
                "google_domain": settings.SERPAPI_GOOGLE_DOMAIN,
                "gl": settings.SERPAPI_COUNTRY,
                "hl": "en",
                "api_key": settings.SERPAPI_KEY,
            },
            timeout=self._timeout_seconds,
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _normalize(raw: dict) -> NormalizedListing | None:
        price = raw.get("extracted_price")
        title = raw.get("title")
        source = raw.get("source")
        if price is None or not title or not source:
            # Missing any of these means it isn't usable as a price-
            # comparison row — skip rather than guess a value.
            return None

        base_url = None
        link = raw.get("product_link") or raw.get("link")
        if link:
            parsed = urlparse(link)
            if parsed.scheme and parsed.netloc:
                base_url = f"{parsed.scheme}://{parsed.netloc}"

        return NormalizedListing(
            product_name=title,
            retailer_name=source,
            price=float(price),
            # SerpApi's `delivery` field is unstructured free text (e.g.
            # "Free delivery", "R50 shipping") — not reliably parseable
            # into a number, so it's surfaced nowhere and delivery_cost
            # stays 0.0 rather than a fabricated guess.
            delivery_cost=0.0,
            retailer_base_url=base_url,
            # Google Shopping doesn't return structured colour/size or a
            # physical store location for most listings — left None
            # rather than scraped out of the free-text title, which would
            # be exactly the kind of fabricated attribute this project
            # explicitly avoids (see geo.py's distance-never-fabricated
            # rule, same principle).
        )
