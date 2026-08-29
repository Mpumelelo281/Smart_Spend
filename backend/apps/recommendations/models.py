"""Entities: Preference, Recommendation (2 of the 11).

The scikit-learn hybrid recommender and its rule-based cold-start fallback
(Rule 5) are Sprint 3 work. `Recommendation.was_accepted` is scaffolded now
because it is the model's training signal — without it captured from day
one, the ranking can never improve past the cold-start fallback.
"""

import uuid

from django.db import models

from apps.accounts.models import StudentProfile
from apps.catalog.models import Product


class Preference(models.Model):
    preference_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="preferences")
    pref_type = models.CharField(max_length=40)
    pref_value = models.CharField(max_length=120)
    radius_km = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "preference"

    def __str__(self):
        return f"{self.pref_type}={self.pref_value}"


class Recommendation(models.Model):
    recommendation_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="recommendations")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="recommendations")
    rank_position = models.PositiveSmallIntegerField()
    # Null = not yet acted on; True/False once the student accepts or
    # dismisses it. This is the model's training signal.
    was_accepted = models.BooleanField(null=True, blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "recommendation"
        indexes = [models.Index(fields=["issued_at"])]

    def __str__(self):
        return f"#{self.rank_position} {self.product_id} -> {self.profile_id}"
