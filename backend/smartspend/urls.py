from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/budgets/", include("apps.budgets.urls")),
    path("api/v1/catalog/", include("apps.catalog.urls")),
    path("api/v1/notifications/", include("apps.notifications.urls")),
    path("api/v1/recommendations/", include("apps.recommendations.urls")),
    path("api/v1/reporting/", include("apps.reporting.urls")),
]
