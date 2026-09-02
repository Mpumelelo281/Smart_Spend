"""Distance-from-… for search results.

Two sources of "where is the student", in priority order:
  1. Real browser geolocation (navigator.geolocation, opt-in, sent as
     ?lat=&lon= — see ProductSearchView) when the student allows it.
  2. A lookup from the free-text `StudentProfile.campus` they typed at
     registration, mapping DUT's actual campus names to coordinates, used
     only when (1) isn't available (permission denied, unsupported
     browser, or the request just didn't include coordinates).
An unrecognised campus string (typo, or a campus not in this list), with
no browser coordinates either, simply gets no distance in results — never
a fabricated one.
"""

import math
from decimal import Decimal

# Approximate coordinates of DUT's campuses (Durban / Pietermaritzburg).
CAMPUS_COORDINATES = {
    "steve biko": (-29.8493, 31.0090),
    "city": (-29.8583, 31.0197),
    "ml sultan": (-29.8583, 31.0197),
    "berea": (-29.8394, 30.9931),
    "ritson": (-29.8394, 30.9931),
    "brickfield": (-29.8580, 31.0010),
    "riverside": (-29.6197, 30.3958),
    "indumiso": (-29.6167, 30.3667),
}

EARTH_RADIUS_KM = 6371


def normalise_campus(campus: str) -> str:
    return (campus or "").strip().lower()


def campus_coordinates(campus: str):
    return CAMPUS_COORDINATES.get(normalise_campus(campus))


def haversine_km(lat1, lon1, lat2, lon2) -> Decimal:
    lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return Decimal(str(round(EARTH_RADIUS_KM * c, 1)))


def distance_from_point_km(lat, lon, retailer):
    """Real-geolocation variant. Returns None only if the retailer itself
    has no store coordinates (e.g. an online-only retailer) — the origin
    is trusted as given.
    """
    if retailer.latitude is None or retailer.longitude is None:
        return None
    return haversine_km(lat, lon, retailer.latitude, retailer.longitude)


def distance_from_campus_km(campus: str, retailer):
    """Returns a Decimal km distance, or None if either endpoint is unknown."""
    origin = campus_coordinates(campus)
    if origin is None or retailer.latitude is None or retailer.longitude is None:
        return None
    return haversine_km(origin[0], origin[1], retailer.latitude, retailer.longitude)


def resolve_distance_km(campus: str, lat, lon, retailer):
    """Prefers real coordinates (lat/lon both present and parseable) over
    the campus lookup — see module docstring for the priority order.
    """
    if lat is not None and lon is not None:
        try:
            return distance_from_point_km(float(lat), float(lon), retailer)
        except (TypeError, ValueError):
            pass  # fall through to the campus lookup
    return distance_from_campus_km(campus, retailer)
