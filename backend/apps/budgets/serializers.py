import logging
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.db.models.functions import Coalesce
from rest_framework import serializers

from .models import Budget, BudgetCategory, Transaction
from .tasks import dispatch_threshold_check

logger = logging.getLogger(__name__)


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


class BudgetCategoryCreateSerializer(serializers.Serializer):
    """Ad-hoc category creation for the "Other" option in the log-expense
    form — spend that doesn't fit anything the student pre-allocated.
    Distinct from BudgetCategoryInputSerializer (which requires an
    allocated_amount because it feeds Rule 1's allowance check at budget
    creation time): an ad-hoc category always starts at R0 allocated, so it
    never touches Budget.total_allocated or the allowance comparison — it
    just gives that spend somewhere to go. Re-selecting a name that already
    exists on the budget returns the existing category instead of erroring,
    so retyping the same "Other" category twice doesn't fragment spend
    across duplicate rows.
    """

    name = serializers.CharField(max_length=60)

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Category name is required.")
        return value

    def create(self, validated_data):
        budget = self.context["budget"]
        name = validated_data["name"]

        existing = BudgetCategory.objects.filter(budget=budget, name__iexact=name).first()
        if existing is not None:
            return existing

        return BudgetCategory.objects.create(budget=budget, name=name, allocated_amount=Decimal("0"))


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
        # Rule 10: "never delays the response" — the threshold check
        # normally runs on a Celery worker, not inline here (see tasks.py).
        # But Rule 10 also requires the alert to actually fire, and .delay()
        # only *enqueues* the check — if no broker/worker is reachable
        # (e.g. local dev without Redis running), the task is silently
        # never picked up and the alert never happens. Falling back to
        # running it inline here trades away the "never blocks" property
        # only in that already-degraded case, which is strictly better
        # than an alert that silently never fires at all.
        try:
            dispatch_threshold_check.delay(instance.category_id)
        except Exception:  # pylint: disable=broad-except
            logger.warning(
                "Could not enqueue dispatch_threshold_check (no Celery broker reachable?) — "
                "running the threshold check inline instead."
            )
            dispatch_threshold_check(instance.category_id)
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


class BudgetCloneSerializer(serializers.Serializer):
    """Recurring-budget convenience: clone an existing budget's category
    allocations into a new month instead of re-typing them. Validation
    mirrors BudgetCreateSerializer's exactly — cloning doesn't get to skip
    Rule 1 just because these numbers were valid once already; the
    student's allowance may have changed since.
    """

    month = serializers.IntegerField(min_value=1, max_value=12)
    year = serializers.IntegerField(min_value=2024)

    def validate(self, attrs):
        source = self.context["source_budget"]
        profile = self.context["profile"]

        if Budget.objects.filter(profile=profile, month=attrs["month"], year=attrs["year"]).exists():
            raise serializers.ValidationError(
                {
                    "non_field_errors": (
                        "A budget already exists for that month; edit it instead of cloning into it."
                    )
                }
            )

        categories = list(source.categories.values("name", "allocated_amount"))
        if not categories:
            raise serializers.ValidationError(
                {"non_field_errors": "The source budget has no categories to clone."}
            )

        total = sum((c["allocated_amount"] for c in categories), Decimal("0"))
        if total > profile.allowance_amount:
            raise serializers.ValidationError(
                {
                    "non_field_errors": (
                        f"Cloned allocations total R{total}, which exceeds your "
                        f"R{profile.allowance_amount} monthly allowance — edit the source budget first."
                    )
                }
            )

        attrs["categories"] = categories
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
