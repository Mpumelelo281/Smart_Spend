from django.urls import path

from . import views

app_name = "reporting"

urlpatterns = [
    path("category-spend/", views.CategorySpendReportView.as_view(), name="category-spend"),
    path("budget-utilization/", views.BudgetUtilizationReportView.as_view(), name="budget-utilization"),
]
