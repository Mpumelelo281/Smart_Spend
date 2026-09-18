"""Rule 9 (RBAC server-side) applied to Rule 7 (k-anonymity): these views
add the "only Administrator/Student Services Officer may call this" check
on top of data that PostgreSQL itself already restricts at the connection
level (see models.py and smartspend/db_router.py) — belt and braces, not
either/or.
"""

from rest_framework import generics, permissions

from apps.accounts.permissions import IsAdministratorOrStudentServices

from .models import BudgetUtilizationSummary, CategorySpendSummary
from .serializers import BudgetUtilizationSummarySerializer, CategorySpendSummarySerializer


class CategorySpendReportView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsAdministratorOrStudentServices]
    serializer_class = CategorySpendSummarySerializer
    # A bare array — Student Services reads these as a small, already
    # k-anonymity-suppressed table, not a paginated feed.
    pagination_class = None

    def get_queryset(self):
        queryset = CategorySpendSummary.objects.order_by("-year", "-month", "campus", "category_name")
        year = self.request.query_params.get("year")
        campus = self.request.query_params.get("campus")
        if year:
            queryset = queryset.filter(year=year)
        if campus:
            queryset = queryset.filter(campus__iexact=campus)
        return queryset


class BudgetUtilizationReportView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsAdministratorOrStudentServices]
    serializer_class = BudgetUtilizationSummarySerializer
    pagination_class = None

    def get_queryset(self):
        queryset = BudgetUtilizationSummary.objects.order_by("-year", "-month", "campus")
        year = self.request.query_params.get("year")
        if year:
            queryset = queryset.filter(year=year)
        return queryset
