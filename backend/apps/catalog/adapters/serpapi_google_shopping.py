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

# Google Shopping is a global aggregator — `gl`/`google_domain` bias the
# result *language and currency*, not which country the seller actually
# operates in, so a plain query still surfaces genuine overseas retailers
# (a UK or Australian shop that happens to also list on google.co.za).
# There's no reliable "seller country" field in SerpApi's response to
# filter on directly, so this is a best-effort signal from the one thing
# we do get: the listing's own domain. A country-code TLD is strong
# evidence (an actual .co.uk store isn't South African); a generic TLD
# (.com, .co, .africa, ...) proves nothing either way and is let through
# rather than guessed at — same "don't fabricate" principle as
# NormalizedListing's other optional fields. Whatever slips past this can
# still be hidden by flipping Retailer.is_active off in the admin.
_NON_SOUTH_AFRICAN_TLDS = {
    # Common ccTLDs likely to actually show up in a South African grocery/
    # retail search. Note "sa" here is Saudi Arabia's ccTLD, not South
    # Africa's (that's "za") — an easy mix-up.
    "uk", "co.uk", "org.uk", "au", "com.au", "net.au", "nz", "co.nz",
    "ca", "us", "de", "fr", "es", "it", "nl", "ie", "be", "ch", "at",
    "se", "no", "dk", "fi", "pl", "pt", "gr", "cz", "hu", "ru",
    "cn", "jp", "co.jp", "in", "co.in", "hk", "sg", "com.sg", "my",
    "com.my", "br", "com.br", "mx", "com.mx", "tr", "ae", "sa", "eg",
    "ng", "com.ng", "ke", "co.ke",
}


def _is_south_african_domain(base_url: str | None) -> bool:
    """True unless the domain carries a *non*-South-African ccTLD — see the
    module-level comment above for why this is "innocent until proven
    foreign" rather than an allowlist."""
    if not base_url:
        return True
    host = urlparse(base_url).netloc.lower().removeprefix("www.")
    labels = host.split(".")
    # Check both the last label (.com) and the last two (.co.uk) — ccTLDs
    # are sometimes a single label, sometimes a second-level + country pair.
    candidates = {labels[-1], ".".join(labels[-2:])} if len(labels) >= 2 else {host}
    return candidates.isdisjoint(_NON_SOUTH_AFRICAN_TLDS)


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
                "location": settings.SERPAPI_LOCATION,
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

        if not _is_south_african_domain(base_url):
            return None

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
