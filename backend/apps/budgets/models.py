"""Entities: Budget, BudgetCategory, Transaction (3 of the 11).

Rule 1 ("allocations must not exceed the allowance") is enforced in
serializers.py, not here — CheckConstraints below catch the cheaper,
context-free half of that rule (no negative money) at the database layer;
the allowance comparison needs to read StudentProfile.allowance_amount,
which is business logic, not a row-level invariant a CHECK constraint can
see.
"""

import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.accounts.models import StudentProfile


class Budget(models.Model):
    budget_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="budgets")
    month = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    year = models.PositiveSmallIntegerField(validators=[MinValueValidator(2024)])
    # Denormalised sum of BudgetCategory.allocated_amount, kept in sync by
    # BudgetSerializer inside a transaction — read-heavy dashboards (and the
    # Rule 1 check itself) would otherwise re-aggregate categories on every
    # request.
    total_allocated = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "budget"
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "month", "year"], name="one_budget_per_student_per_month"
            ),
            models.CheckConstraint(
                check=models.Q(total_allocated__gte=0), name="budget_total_non_negative"
            ),
        ]

    def __str__(self):
        return f"Budget<{self.profile_id} {self.month}/{self.year}>"


class BudgetCategory(models.Model):
    category_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=60)
    allocated_amount = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        db_table = "budget_category"
        constraints = [
            models.CheckConstraint(
                check=models.Q(allocated_amount__gte=0), name="category_amount_non_negative"
            ),
            models.UniqueConstraint(fields=["budget", "name"], name="unique_category_name_per_budget"),
        ]

    def __str__(self):
        return f"{self.name} (R{self.allocated_amount})"


class Transaction(models.Model):
    transaction_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(BudgetCategory, on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    purchase_date = models.DateField()
    description = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "transaction"
        constraints = [
            models.CheckConstraint(check=models.Q(amount__gte=0), name="transaction_amount_non_negative"),
        ]
        indexes = [models.Index(fields=["purchase_date"])]

    def __str__(self):
        return f"R{self.amount} on {self.purchase_date}"
