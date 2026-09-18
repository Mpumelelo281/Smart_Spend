"""Rule 5's cold-start fallback: a rule-based recommender that runs with no
training data at all, so a brand-new student sees useful recommendations on
day one rather than an empty page while waiting for the scikit-learn hybrid
model (still Sprint 3 work — see the module docstring in models.py).

Ranking signal, in priority order:
  1. Categories the student explicitly said they care about (Preference
     rows with pref_type="category").
  2. Failing that, the categories they've already budgeted for this month —
     a student who allocated money to "Groceries" is implicitly telling us
     they buy groceries, even if they never opened a preferences screen.
  3. Failing that (a genuinely new student with no budget yet), every
     category — better to show *something* cheap and nearby than nothing.

Within that category set, products are ranked by total landed cost
ascending (cheapest first — same Rule 3 principle as search), optionally
narrowed by a Preference(pref_type="location", radius_km=...) the same way
ProductSearchView narrows by radius_km. `was_accepted` is never set here —
only RecommendationFeedbackView sets it, from real student action.
"""

from django.db.models import OuterRef, Subquery

from apps.catalog.geo import resolve_distance_km
from apps.catalog.models import PriceRecord, Product

from .models import Preference, Recommendation

DEFAULT_LIMIT = 10


def _interest_categories(profile) -> list[str]:
    preferred = list(
        Preference.objects.filter(profile=profile, pref_type="category").values_list(
            "pref_value", flat=True
        )
    )
    if preferred:
        return preferred

    budgeted = list(
        profile.budgets.order_by("-year", "-month")
        .first()
        .categories.values_list("name", flat=True)
        if profile.budgets.exists()
        else []
    )
    return budgeted


def _radius_km(profile):
    pref = Preference.objects.filter(profile=profile, pref_type="location").exclude(
        radius_km__isnull=True
    ).first()
    return float(pref.radius_km) if pref else None


def generate_for_profile(profile, limit: int = DEFAULT_LIMIT) -> list[Recommendation]:
    """Regenerates the student's *pending* recommendation batch (any row
    they haven't yet accepted or dismissed) and returns the new rows,
    best-ranked first. Rows already actioned (was_accepted is not null)
    are left alone — they're the model's future training signal and must
    survive a regeneration.
    """
    categories = _interest_categories(profile)
    radius_km = _radius_km(profile)

    latest_per_product_retailer = (
        PriceRecord.objects.filter(product=OuterRef("product"), retailer=OuterRef("retailer"))
        .order_by("-retrieved_at")
        .values("price_id")[:1]
    )
    records = (
        PriceRecord.objects.select_related("product", "retailer")
        .filter(retailer__is_active=True, price_id=Subquery(latest_per_product_retailer))
        .order_by("price", "delivery_cost")
    )
    if categories:
        records = records.filter(product__category__in=categories)

    seen_products: set = set()
    ranked_product_ids: list = []
    for record in records:
        if record.product_id in seen_products:
            continue
        if radius_km is not None:
            distance = resolve_distance_km(profile.campus, None, None, record.retailer)
            if distance is not None and float(distance) > radius_km:
                continue
        seen_products.add(record.product_id)
        ranked_product_ids.append(record.product_id)
        if len(ranked_product_ids) >= limit:
            break

    Recommendation.objects.filter(profile=profile, was_accepted__isnull=True).delete()
    new_rows = [
        Recommendation(profile=profile, product_id=product_id, rank_position=position)
        for position, product_id in enumerate(ranked_product_ids, start=1)
    ]
    Recommendation.objects.bulk_create(new_rows)

    return list(
        Recommendation.objects.select_related("product")
        .filter(profile=profile, was_accepted__isnull=True)
        .order_by("rank_position")
    )


def best_current_offer(product: Product):
    """Cheapest active listing for a product right now — used to show the
    student where to actually buy a recommended product, same landed-cost
    field search results lead with.
    """
    return (
        PriceRecord.objects.select_related("retailer")
        .filter(product=product, retailer__is_active=True)
        .order_by("price", "delivery_cost")
        .first()
    )
