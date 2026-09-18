from django.urls import path

from . import views

app_name = "recommendations"

urlpatterns = [
    path("", views.RecommendationListView.as_view(), name="recommendation-list"),
    path(
        "<uuid:recommendation_id>/feedback/",
        views.RecommendationFeedbackView.as_view(),
        name="recommendation-feedback",
    ),
    path("preferences/", views.PreferenceListCreateView.as_view(), name="preference-list-create"),
    path("preferences/<uuid:preference_id>/", views.PreferenceDetailView.as_view(), name="preference-detail"),
]
