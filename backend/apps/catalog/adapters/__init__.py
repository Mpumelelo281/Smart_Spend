from .base import AdapterUnavailable, NormalizedListing, RetailerAdapter
from .checkers import CheckersAdapter
from .mr_price import MrPriceAdapter
from .serpapi_google_shopping import SerpApiGoogleShoppingAdapter
from .shoprite import ShopriteAdapter

# Rule 6: "One adapter interface that every integration implements; adding
# a source must not require redeployment." In practice today that means:
# add a new module implementing RetailerAdapter, append it here. Nothing
# in views.py or live_search.py needs to change — they iterate this list.
# Checkers/Shoprite/Mr Price stay inert (is_configured() False) until their
# *_API_BASE_URL setting is supplied — see each module's docstring.
ACTIVE_ADAPTERS: list[type[RetailerAdapter]] = [
    SerpApiGoogleShoppingAdapter,
    CheckersAdapter,
    ShopriteAdapter,
    MrPriceAdapter,
]

__all__ = ["AdapterUnavailable", "NormalizedListing", "RetailerAdapter", "ACTIVE_ADAPTERS"]
