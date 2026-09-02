"""Bridges the adapter layer (adapters/) to the PriceRecord table the
search view already queries — see views.py. A live refresh doesn't change
what gets *served*; it just makes sure PriceRecord has something fresh in
it before the normal DB query runs. That keeps ProductSearchView's own
logic (sorting, filtering, distance) completely unaware of where the rows
came from.

Rule 4's 15-minute cache lives here as a "have we already tried this exact
query recently" guard — not a cache of the serialized response. The
response is always built fresh from PriceRecord (the durable, queryable
source of truth); the cache only stops the same query from hammering a
live adapter more than once per window.
"""

import logging

from django.core.cache import cache
from django.utils import timezone

from .adapters import ACTIVE_ADAPTERS, AdapterUnavailable, NormalizedListing
from .models import PriceRecord, Product, Retailer

logger = logging.getLogger(__name__)

_CACHE_KEY_PREFIX = "catalog:live-search-attempted:"


def _cache_key(query: str) -> str:
    return f"{_CACHE_KEY_PREFIX}{query.strip().lower()}"


def _persist(listing: NormalizedListing) -> None:
    retailer, _ = Retailer.objects.get_or_create(
        name=listing.retailer_name,
        defaults={
            "integration_type": Retailer.IntegrationType.API,
            "base_url": listing.retailer_base_url or "",
            "store_address": listing.store_address or "",
            "latitude": listing.latitude,
            "longitude": listing.longitude,
            "is_active": True,
        },
    )
    raw_attributes = {"color": listing.color, "size": listing.size}
    attributes = {key: value for key, value in raw_attributes.items() if value}
    product, _ = Product.objects.get_or_create(
        name=listing.product_name,
        category=listing.category or "General",
        defaults={"attributes": attributes},
    )
    # A fresh row per refresh, deliberately — see the module docstring on
    # PriceRecord in models.py: "the fact of interest is the price *at
    # this moment*". ProductSearchView dedupes to the newest row per
    # (product, retailer) at query time, so old snapshots stay queryable
    # history without cluttering search results.
    PriceRecord.objects.create(
        product=product,
        retailer=retailer,
        price=listing.price,
        delivery_cost=listing.delivery_cost,
        retrieved_at=timezone.now(),
    )


def ensure_live_data(query: str) -> None:
    """No-op for a blank query (browsing, not searching) or when nothing
    is configured — the seeded/previously-fetched PriceRecord rows are
    still served either way, just not refreshed this time.
    """
    query = query.strip()
    if not query:
        return

    cache_key = _cache_key(query)
    if cache.get(cache_key):
        return

    attempted_any = False
    for adapter_cls in ACTIVE_ADAPTERS:
        adapter = adapter_cls()
        if not adapter.is_configured():
            continue
        attempted_any = True
        try:
            listings = adapter.search(query)
        except AdapterUnavailable as exc:
            # NFR Availability: "serve cached prices with a visible
            # staleness indicator when a live source is unreachable" —
            # the "visible" part is that PriceRecord.retrieved_at on
            # whatever's already there tells the truth; nothing here
            # pretends the refresh succeeded.
            logger.warning("Retailer adapter %s unavailable: %s", adapter.name, exc)
            continue

        for listing in listings:
            _persist(listing)

    if attempted_any:
        cache.set(cache_key, True, timeout=900)  # Rule 4: 15 minutes.
