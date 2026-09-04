from django.urls import path

from . import views

app_name = "budgets"

urlpatterns = [
    path("", views.BudgetListCreateView.as_view(), name="budget-list-create"),
    path("<uuid:pk>/", views.BudgetDetailView.as_view(), name="budget-detail"),
    path("<uuid:budget_id>/categories/", views.BudgetCategoryCreateView.as_view(), name="budget-category-create"),
    path("transactions/", views.TransactionCreateView.as_view(), name="transaction-create"),
]
