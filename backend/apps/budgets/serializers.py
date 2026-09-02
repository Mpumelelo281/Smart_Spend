from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.db.models.functions import Coalesce
from rest_framework import serializers

from .models import Budget, BudgetCategory, Transaction
from .notifications import check_category_threshold


class BudgetCategoryInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=60)
    allocated_amount = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=Decimal("0"))


class BudgetCategorySerializer(serializers.ModelSerializer):
    # Spending-history feature: how much of this category has actually been
    # spent, vs. allocated_amount. A handful of categories per budget, so a
    # per-object aggregate here is fine — worth revisiting with a
    # Prefetch+annotate if this ever serializes hundreds of categories at
    # once (e.g. a Student Services report, not a single student's budget).
    spent_amount = serializers.SerializerMethodField()

    class Meta:
        model = BudgetCategory
        fields = ["category_id", "name", "allocated_amount", "spent_amount"]

    def get_spent_amount(self, obj):
        return obj.transactions.aggregate(total=Coalesce(Sum("amount"), Decimal("0")))["total"]


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ["transaction_id", "category", "amount", "purchase_date", "description"]

    def validate_category(self, category):
        request = self.context["request"]
        if category.budget.profile.user_id != request.user.user_id:
            raise serializers.ValidationError("You may only log transactions against your own budget.")
        return category

    def create(self, validated_data):
        instance = super().create(validated_data)
        # Rule 10. Synchronous for now — see apps/notifications/models.py.
        check_category_threshold(instance.category)
        return instance


class BudgetSerializer(serializers.ModelSerializer):
    categories = BudgetCategorySerializer(many=True, read_only=True)
    total_spent = serializers.SerializerMethodField()

    class Meta:
        model = Budget
        fields = [
            "budget_id",
            "month",
            "year",
            "total_allocated",
            "total_spent",
            "categories",
            "created_at",
        ]

    def get_total_spent(self, obj):
        return Transaction.objects.filter(category__budget=obj).aggregate(
            total=Coalesce(Sum("amount"), Decimal("0"))
        )["total"]


class BudgetCreateSerializer(serializers.Serializer):
    """
    Rule 1: "Allocations must not exceed the allowance ... enforced
    server-side only — the client may preview it, but the server is
    authoritative." This is that server-side enforcement; the React budget
    setup screen re-implements the same sum-vs-allowance check purely so
    the student sees the error before submitting, per Rule 2.
    """

    month = serializers.IntegerField(min_value=1, max_value=12)
    year = serializers.IntegerField(min_value=2024)
    categories = BudgetCategoryInputSerializer(many=True, min_length=1)

    def validate(self, attrs):
        profile = self.context["profile"]

        if Budget.objects.filter(profile=profile, month=attrs["month"], year=attrs["year"]).exists():
            raise serializers.ValidationError(
                {
                    "non_field_errors": (
                        "A budget already exists for that month; edit it instead of creating another."
                    )
                }
            )

        total = sum((c["allocated_amount"] for c in attrs["categories"]), Decimal("0"))

        if total > profile.allowance_amount:
            raise serializers.ValidationError(
                {
                    "categories": (
                        f"Category allocations total R{total}, which exceeds your "
                        f"R{profile.allowance_amount} monthly allowance."
                    )
                }
            )

        names = [c["name"].strip().lower() for c in attrs["categories"]]
        if len(names) != len(set(names)):
            raise serializers.ValidationError(
                {"categories": "Category names must be unique within a budget."}
            )

        attrs["total_allocated"] = total
        return attrs

    def create(self, validated_data):
        profile = self.context["profile"]
        categories_data = validated_data.pop("categories")

        with transaction.atomic():
            budget = Budget.objects.create(
                profile=profile,
                month=validated_data["month"],
                year=validated_data["year"],
                total_allocated=validated_data["total_allocated"],
            )
            BudgetCategory.objects.bulk_create(
                [
                    BudgetCategory(budget=budget, name=c["name"], allocated_amount=c["allocated_amount"])
                    for c in categories_data
                ]
            )
        return budget
