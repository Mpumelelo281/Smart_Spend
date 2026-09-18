"""Mr Price product search adapter — same shape and caveats as
checkers.py (see that module's docstring): a configurable JSON search
endpoint (MR_PRICE_API_BASE_URL), inert until configured, with a
`_normalize` field mapping that must be verified against the real endpoint
before this is enabled anywhere. Mr Price also publishes colour/size on
most listings (clothing/homeware), unlike a grocery retailer, so those are
carried through when present instead of left None.
"""

import logging

import pybreaker
import requests
from django.conf import settings

from .base import AdapterUnavailable, NormalizedListing, RetailerAdapter

logger = logging.getLogger(__name__)

_breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=60)


class MrPriceAdapter(RetailerAdapter):
    name = "mr_price"
    _timeout_seconds = 8

    def is_configured(self) -> bool:
        return bool(settings.MR_PRICE_API_BASE_URL)

    def search(self, query: str) -> list[NormalizedListing]:
        if not self.is_configured():
            raise AdapterUnavailable("MR_PRICE_API_BASE_URL is not set.")

        try:
            data = self._call_api(query)
        except pybreaker.CircuitBreakerError as exc:
            raise AdapterUnavailable("Circuit open: Mr Price has failed repeatedly recently.") from exc
        except requests.RequestException as exc:
            raise AdapterUnavailable(f"Mr Price request failed: {exc}") from exc

        return [listing for raw in data.get("results", []) if (listing := self._normalize(raw))]

    @_breaker
    def _call_api(self, query: str) -> dict:
        headers = {}
        if settings.MR_PRICE_API_KEY:
            headers["Authorization"] = f"Bearer {settings.MR_PRICE_API_KEY}"

        response = requests.get(
            settings.MR_PRICE_API_BASE_URL,
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
            retailer_name="Mr Price",
            price=float(price),
            delivery_cost=float(raw.get("delivery_cost") or 0.0),
            category=raw.get("category"),
            color=raw.get("colour") or raw.get("color"),
            size=raw.get("size"),
            retailer_base_url="https://www.mrp.com",
        )
