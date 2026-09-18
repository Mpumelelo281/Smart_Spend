"""Unmanaged models over the anonymised materialised views created by
infra/sql/002_reporting_views.sql — never migrated by Django (see
smartspend.db_router.ReportingRouter.allow_migrate, which returns False for
this app's label) and only ever read through the `reporting` database
alias, which PostgreSQL restricts at the grant level (infra/sql/001_init_roles.sql)
to exactly these two views. Rule 7: every row here has already passed the
k-anonymity HAVING clause in the SQL itself — student_count is never below
settings.K_ANONYMITY_THRESHOLD, so nothing in this app needs to re-check
that.

`id` is a synthetic row_number(), not a meaningful identifier — Django
requires every model to have a primary key, and none of these aggregate
rows has a natural single-column one.
"""

from django.db import models


class CategorySpendSummary(models.Model):
    id = models.BigIntegerField(primary_key=True)
    campus = models.CharField(max_length=120)
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()
    category_name = models.CharField(max_length=60)
    student_count = models.PositiveIntegerField()
    total_spent = models.DecimalField(max_digits=10, decimal_places=2)
    avg_transaction_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_allocated = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        app_label = "reporting"
        managed = False
        db_table = "reporting_category_spend_summary"

    def __str__(self):
        return f"{self.campus} {self.month}/{self.year} {self.category_name}"


class BudgetUtilizationSummary(models.Model):
    id = models.BigIntegerField(primary_key=True)
    campus = models.CharField(max_length=120)
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()
    student_count = models.PositiveIntegerField()
    total_allocated = models.DecimalField(max_digits=10, decimal_places=2)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        app_label = "reporting"
        managed = False
        db_table = "reporting_budget_utilization_summary"

    def __str__(self):
        return f"{self.campus} {self.month}/{self.year}"
