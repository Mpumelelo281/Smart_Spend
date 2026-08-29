from django.contrib import admin

from .models import Preference, Recommendation


@admin.register(Preference)
class PreferenceAdmin(admin.ModelAdmin):
    list_display = ["profile", "pref_type", "pref_value", "radius_km"]
    list_filter = ["pref_type"]


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ["profile", "product", "rank_position", "was_accepted", "issued_at"]
    list_filter = ["was_accepted"]
