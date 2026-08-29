from django.contrib import admin

from .models import Budget, BudgetCategory, Transaction


class BudgetCategoryInline(admin.TabularInline):
    model = BudgetCategory
    extra = 0


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ["budget_id", "profile", "month", "year", "total_allocated"]
    list_filter = ["year", "month"]
    inlines = [BudgetCategoryInline]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ["transaction_id", "category", "amount", "purchase_date"]
    list_filter = ["purchase_date"]
