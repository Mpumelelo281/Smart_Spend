from django.urls import path

from . import views

app_name = "budgets"

urlpatterns = [
    path("", views.BudgetListCreateView.as_view(), name="budget-list-create"),
    path("<uuid:pk>/", views.BudgetDetailView.as_view(), name="budget-detail"),
    path("transactions/", views.TransactionCreateView.as_view(), name="transaction-create"),
]
