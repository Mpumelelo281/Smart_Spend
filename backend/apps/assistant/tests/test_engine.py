from datetime import date
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.assistant import engine
from apps.budgets.models import Budget, BudgetCategory, Transaction

pytestmark = pytest.mark.django_db


@pytest.fixture
def profile(student_user):
    return student_user.student_profile


def _make_budget(profile, year, month, categories):
    """categories: {name: (allocated, [spent_amounts])}"""
    budget = Budget.objects.create(profile=profile, year=year, month=month, total_allocated=0)
    total = Decimal("0")
    for name, (allocated, spends) in categories.items():
        category = BudgetCategory.objects.create(budget=budget, name=name, allocated_amount=allocated)
        total += Decimal(allocated)
        for i, amount in enumerate(spends):
            Transaction.objects.create(
                category=category,
                amount=Decimal(amount),
                purchase_date=date(year, month, min(i + 1, 28)),
            )
    budget.total_allocated = total
    budget.save(update_fields=["total_allocated"])
    return budget


@pytest.fixture
def this_month_budget(profile):
    today = timezone.localdate()
    return _make_budget(
        profile,
        today.year,
        today.month,
        {
            "Food": ("500.00", ["245.00", "100.00"]),
            "Transport": ("300.00", ["350.00"]),  # over budget
        },
    )


class TestGreetingAndFallback:
    def test_greeting(self, profile):
        result = engine.answer("Hi", profile)
        assert result.intent == "greeting"
        assert "SpendWise" in result.reply
        assert result.quick_replies

    def test_unrecognised_message_falls_back_to_help(self, profile):
        result = engine.answer("what's the weather like", profile)
        assert result.intent == "fallback"
        assert "How much did I spend" in result.reply


class TestSpendByCategory:
    def test_known_category(self, this_month_budget, profile):
        result = engine.answer("How much did I spend on food this month?", profile)
        assert result.intent == "spend_by_category"
        assert "R345.00" in result.reply  # 245 + 100
        assert "Food" in result.reply

    def test_unknown_category_falls_back_to_total(self, this_month_budget, profile):
        result = engine.answer("How much did I spend on textbooks?", profile)
        assert result.intent == "spend_by_category"
        assert "R695.00" in result.reply  # 345 + 350 total

    def test_no_budget_yet(self, profile):
        result = engine.answer("How much did I spend on food?", profile)
        assert "don't have a budget" in result.reply


class TestAffordCheck:
    def test_can_afford_within_category_remaining(self, this_month_budget, profile):
        result = engine.answer("Can I afford to spend R100 on food?", profile)
        assert result.intent == "afford_check"
        assert result.reply.startswith("Yes")
        assert "R155.00" in result.reply  # 500 - 345 remaining

    def test_cannot_afford_overspent_category(self, this_month_budget, profile):
        result = engine.answer("Can I afford to spend R50 on transport?", profile)
        assert "tight" in result.reply

    def test_missing_amount_asks_for_one(self, this_month_budget, profile):
        result = engine.answer("Can I afford new clothes?", profile)
        assert "How much are you thinking" in result.reply


class TestOverspend:
    def test_flags_the_category_over_its_allocation(self, this_month_budget, profile):
        result = engine.answer("Where am I spending too much?", profile)
        assert result.intent == "overspend"
        assert "Transport" in result.reply
        assert "R350.00" in result.reply


class TestWhyIncrease:
    def test_compares_against_last_month(self, profile):
        today = timezone.localdate()
        prev_year, prev_month = engine._shift_month(today.year, today.month, -1)
        _make_budget(profile, prev_year, prev_month, {"Food": ("500.00", ["100.00"])})
        _make_budget(profile, today.year, today.month, {"Food": ("500.00", ["400.00"])})

        result = engine.answer("Why did I spend more this month?", profile)
        assert result.intent == "why_increase"
        assert "R300.00" in result.reply
        assert "Food" in result.reply

    def test_no_previous_month_data(self, this_month_budget, profile):
        result = engine.answer("Why did I spend more this month?", profile)
        assert "don't have last month's budget" in result.reply


class TestSavingsGoal:
    def test_computes_monthly_amount_with_explicit_months(self, profile):
        result = engine.answer("Help me save R5000 in 8 months", profile)
        assert result.intent == "savings_goal"
        assert "R625.00" in result.reply
        assert "8 months" in result.reply

    def test_defaults_timeframe_when_unspecified(self, profile):
        result = engine.answer("Help me save R1200", profile)
        assert f"{engine.DEFAULT_SAVINGS_MONTHS} months" in result.reply
        assert "assuming" in result.reply.lower()

    def test_missing_amount_asks_for_one(self, profile):
        result = engine.answer("Help me save", profile)
        assert "How much would you like to save" in result.reply


class TestAlerts:
    def test_no_alerts(self, profile):
        result = engine.answer("Any spending alerts?", profile)
        assert result.intent == "alerts"
        assert "No active budget alerts" in result.reply


class TestBudgetStatus:
    def test_reports_remaining(self, this_month_budget, profile):
        result = engine.answer("How much budget do I have left?", profile)
        assert result.intent == "budget_status"
        assert "R105.00" in result.reply  # 800 allocated - 695 spent


class TestSearchTransactions:
    def test_filters_by_threshold(self, this_month_budget, profile):
        result = engine.answer("Find transactions over R200", profile)
        assert result.intent == "search_transactions"
        assert "R245.00" in result.reply
        assert "R350.00" in result.reply
        assert "R100.00" not in result.reply
