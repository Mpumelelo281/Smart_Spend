from django.urls import path

from . import views

app_name = "budgets"

urlpatterns = [
    path("", views.BudgetListCreateView.as_view(), name="budget-list-create"),
    path("export/", views.BudgetHistoryExportView.as_view(), name="budget-history-export"),
    path("<uuid:pk>/", views.BudgetDetailView.as_view(), name="budget-detail"),
    path("<uuid:pk>/clone/", views.BudgetCloneView.as_view(), name="budget-clone"),
    path("<uuid:pk>/forecast/", views.BudgetForecastView.as_view(), name="budget-forecast"),
    path(
        "<uuid:budget_id>/categories/",
        views.BudgetCategoryCreateView.as_view(),
        name="budget-category-create",
    ),
    path("transactions/", views.TransactionCreateView.as_view(), name="transaction-create"),
]
