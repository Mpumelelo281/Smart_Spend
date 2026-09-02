from .base import AdapterUnavailable, NormalizedListing, RetailerAdapter
from .serpapi_google_shopping import SerpApiGoogleShoppingAdapter

# Rule 6: "One adapter interface that every integration implements; adding
# a source must not require redeployment." In practice today that means:
# add a new module implementing RetailerAdapter, append it here. Nothing
# in views.py or live_search.py needs to change — they iterate this list.
ACTIVE_ADAPTERS: list[type[RetailerAdapter]] = [SerpApiGoogleShoppingAdapter]

__all__ = ["AdapterUnavailable", "NormalizedListing", "RetailerAdapter", "ACTIVE_ADAPTERS"]
