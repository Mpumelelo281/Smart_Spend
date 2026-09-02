"""Rule 6: "One adapter interface that every integration implements ...
Each adapter sits behind a circuit breaker so a failing source is bypassed
rather than allowed to block search."

A NormalizedListing is deliberately the smallest common shape every
adapter can fill in truthfully. Fields an adapter's source doesn't provide
(e.g. Google Shopping rarely gives a physical store address) stay None —
never guessed, per the same "don't fabricate a distance" rule geo.py
follows.
"""

from dataclasses import dataclass
from typing import Optional


class AdapterUnavailable(Exception):
    """Raised by an adapter when its source can't be reached right now —
    caught by live_search.py, which falls back to whatever is already
    cached in PriceRecord rather than surfacing a 500 to the student.
    """


@dataclass
class NormalizedListing:
    product_name: str
    retailer_name: str
    price: float
    delivery_cost: float = 0.0
    category: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    retailer_base_url: Optional[str] = None
    store_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class RetailerAdapter:
    """Subclass and implement `search`. Never call an external service
    directly from a view or task — always through a `RetailerAdapter`
    subclass, so the circuit breaker and the "never redeploy to add a
    source" rule both actually hold.
    """

    #: Human-readable name for logging/metrics — not shown to students.
    name = "base"

    def is_configured(self) -> bool:
        """Whether this adapter has what it needs (an API key, etc.) to
        run at all. live_search.py skips unconfigured adapters silently —
        a missing key is a deployment gap, not a student-facing error.
        """
        raise NotImplementedError

    def search(self, query: str) -> list[NormalizedListing]:
        raise NotImplementedError
