from rest_framework import serializers

from .models import BudgetUtilizationSummary, CategorySpendSummary


class CategorySpendSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = CategorySpendSummary
        fields = [
            "campus",
            "year",
            "month",
            "category_name",
            "student_count",
            "total_spent",
            "avg_transaction_amount",
            "total_allocated",
        ]
        read_only_fields = fields


class BudgetUtilizationSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetUtilizationSummary
        fields = ["campus", "year", "month", "student_count", "total_allocated", "total_spent"]
        read_only_fields = fields
