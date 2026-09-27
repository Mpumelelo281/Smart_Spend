"""SpendWise — a rule-based chat assistant grounded entirely in the asking
student's own SmartSpend data (their current month's Budget/BudgetCategory/
Transaction rows and unread Notification alerts).

Deliberately not an LLM call: every reply below is a template filled with a
real number pulled straight from the database, so an answer is either
correct or it's a bug — there is nothing to hallucinate, no external API
key, and no per-message cost. `answer()` is the only entry point views.py
needs; everything else here is a private helper, kept as plain functions
(not a class) so each one is independently unit-testable — see
tests/test_engine.py.

Not financial advice: every reply is a description of the student's own
logged data (Rule-based arithmetic over their transactions/budget), not a
recommendation from a qualified adviser — see the disclaimer returned
alongside the greeting, and DISCLAIMER below for reuse elsewhere.
"""

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.budgets.models import Budget, Transaction
from apps.notifications.models import Notification

DISCLAIMER = (
    "SpendWise explains what's already in your SmartSpend data — it's budgeting help, "
    "not professional financial advice."
)

DEFAULT_SAVINGS_MONTHS = 6
SEARCH_RESULT_LIMIT = 5
ALERT_RESULT_LIMIT = 5

QUICK_REPLIES = [
    {"label": "📊 My spending", "message": "How much have I spent this month?"},
    {"label": "💰 My budget", "message": "How much budget do I have left?"},
    {"label": "🎯 Savings goal", "message": "Help me set a savings goal"},
    {"label": "⚠️ Spending alerts", "message": "Any spending alerts?"},
]

_GREETING_RE = re.compile(r"^(hi|hello|hey|howzit|sawubona)[!.\s]*$", re.I)
_WHAT_CAN_YOU_DO_RE = re.compile(
    r"what can you do|what do you do|how (does|do) (this|it|you) work|\bhelp\b$", re.I
)
_ALERT_RE = re.compile(r"\balerts?\b|\bwarn(ing)?s?\b", re.I)
_SAVINGS_RE = re.compile(r"\bsav(e|ing|ings)\b", re.I)
_AFFORD_RE = re.compile(r"\bafford\b", re.I)
_WHY_INCREASE_RE = re.compile(r"\bwhy\b", re.I)
_INCREASE_RE = re.compile(r"\bmore\b|\bincreas", re.I)
_OVERSPEND_RE = re.compile(r"spending too much|overspend|over[\s-]?budget|too much on", re.I)
_SEARCH_RE = re.compile(r"\bfind\b|\bsearch\b|\bshow me\b", re.I)
_BUDGET_STATUS_RE = re.compile(r"\b(remaining|left|balance)\b", re.I)
_SPEND_RE = re.compile(r"\bspen[dt]\b|\bspending\b", re.I)

# The comma-grouped alternative requires an actual comma (`(?:,\d{3})+`,
# one-or-more) so it only fires for "5,000"-style input — otherwise, with
# `*` (zero-or-more), Python's re tries it first and happily matches just
# the first 3 digits of a plain "5000", leaving the rest of the number
# unconsumed.
_AMOUNT_R_RE = re.compile(r"R\s*(\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)", re.I)
_AMOUNT_BARE_RE = re.compile(r"\b(\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)\b(?!\s*months?)")
_MONTHS_RE = re.compile(r"(\d+)\s*months?", re.I)
_OVER_RE = re.compile(r"\b(over|above|more than)\b", re.I)
_UNDER_RE = re.compile(r"\b(under|below|less than)\b", re.I)


@dataclass
class AssistantReply:
    reply: str
    intent: str
    quick_replies: list = field(default_factory=list)


def answer(message: str, profile) -> AssistantReply:  # pylint: disable=too-many-return-statements
    """The one entry point views.py needs. `profile` is the asking
    student's StudentProfile — every lookup below is scoped to it, same
    RBAC pattern as every other student-facing view in this project
    (Rule 9: filtered server-side, not just hidden client-side)."""
    text = (message or "").strip()
    lower = text.lower()

    if _GREETING_RE.match(text):
        return AssistantReply(
            reply=(
                "Hi! I'm SpendWise, your SmartSpend assistant. I can help you understand your "
                f"spending, budget and savings goals. {DISCLAIMER} What would you like to know?"
            ),
            intent="greeting",
            quick_replies=QUICK_REPLIES,
        )

    if _WHAT_CAN_YOU_DO_RE.search(lower):
        return AssistantReply(reply=_help_text(), intent="help", quick_replies=QUICK_REPLIES)

    if _ALERT_RE.search(lower):
        return AssistantReply(reply=_alerts_reply(profile), intent="alerts")

    if _SAVINGS_RE.search(lower):
        return AssistantReply(reply=_savings_reply(text), intent="savings_goal")

    if _AFFORD_RE.search(lower):
        return AssistantReply(reply=_afford_reply(text, profile), intent="afford_check")

    if _WHY_INCREASE_RE.search(lower) and _INCREASE_RE.search(lower):
        return AssistantReply(reply=_why_increase_reply(profile), intent="why_increase")

    if _OVERSPEND_RE.search(lower):
        return AssistantReply(reply=_overspend_reply(profile), intent="overspend")

    if _SEARCH_RE.search(lower):
        return AssistantReply(reply=_search_reply(text, profile), intent="search_transactions")

    if _BUDGET_STATUS_RE.search(lower) and not _SPEND_RE.search(lower):
        return AssistantReply(reply=_budget_status_reply(profile), intent="budget_status")

    if _SPEND_RE.search(lower):
        return AssistantReply(reply=_spend_by_category_reply(text, profile), intent="spend_by_category")

    return AssistantReply(reply=_help_text(), intent="fallback", quick_replies=QUICK_REPLIES)


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def _money(value: Decimal) -> str:
    return f"R{value:,.2f}"


def _total_spent(budget: Budget) -> Decimal:
    return Transaction.objects.filter(category__budget=budget).aggregate(
        total=Coalesce(Sum("amount"), Decimal("0"))
    )["total"]


def _category_spent(category) -> Decimal:
    return category.transactions.aggregate(total=Coalesce(Sum("amount"), Decimal("0")))["total"]


def _shift_month(year: int, month: int, delta: int) -> tuple[int, int]:
    total = year * 12 + (month - 1) + delta
    return total // 12, total % 12 + 1


def _budget_for(profile, year: int, month: int):
    return (
        Budget.objects.filter(profile=profile, year=year, month=month)
        .prefetch_related("categories__transactions")
        .first()
    )


def _current_budget(profile):
    today = timezone.localdate()
    return _budget_for(profile, today.year, today.month)


def _match_category(text: str, categories):
    lower = text.lower()
    # Longest name first so e.g. "Take-out food" wins over a broader "Food"
    # both being substring-matches of the same message.
    for category in sorted(categories, key=lambda c: -len(c.name)):
        if re.search(r"\b" + re.escape(category.name.lower()) + r"\b", lower):
            return category
    return None


def _extract_amount(text: str) -> Decimal | None:
    match = _AMOUNT_R_RE.search(text)
    if not match:
        match = _AMOUNT_BARE_RE.search(text)
    if not match:
        return None
    try:
        return Decimal(match.group(1).replace(",", ""))
    except InvalidOperation:
        return None


def _extract_months(text: str) -> int | None:
    match = _MONTHS_RE.search(text)
    return int(match.group(1)) if match else None


def _extract_threshold(text: str):
    """Returns ("gte"|"lte", Decimal) if the message names a spend
    threshold (e.g. "over R200"), else None."""
    amount = _extract_amount(text)
    if amount is None:
        return None
    if _OVER_RE.search(text):
        return "gte", amount
    if _UNDER_RE.search(text):
        return "lte", amount
    return None


_NO_BUDGET_REPLY = (
    "You don't have a budget set up for this month yet, so I don't have anything to check "
    "against. Set one up under Budget → New budget and I'll be able to answer this."
)


def _help_text() -> str:
    return (
        "I can help with things like:\n"
        "• How much did I spend on food this month?\n"
        "• Can I afford to spend R500 on clothes?\n"
        "• Where am I spending too much?\n"
        "• Why did I spend more this month?\n"
        "• Help me save R5,000\n"
        "• Any spending alerts?\n"
        "What would you like to know?"
    )


# ---------------------------------------------------------------------------
# Intent handlers
# ---------------------------------------------------------------------------

def _alerts_reply(profile) -> str:
    alerts = list(
        Notification.objects.filter(
            profile=profile,
            is_read=False,
            notif_type__in=[
                Notification.NotifType.BUDGET_THRESHOLD_80,
                Notification.NotifType.BUDGET_EXCEEDED,
            ],
        ).order_by("-created_at")[:ALERT_RESULT_LIMIT]
    )
    if not alerts:
        return (
            "No active budget alerts right now — you're within your allocations across every category. "
            "\U0001F389"
        )
    lines = "\n".join(f"• {n.message}" for n in alerts)
    return f"You have {len(alerts)} active alert(s):\n{lines}"


def _savings_reply(text: str) -> str:
    amount = _extract_amount(text)
    if amount is None:
        return (
            "How much would you like to save, and (optionally) over how many months? "
            'For example: "Help me save R5000 in 6 months."'
        )
    months = _extract_months(text)
    assumed_default = months is None
    months = months or DEFAULT_SAVINGS_MONTHS
    monthly = (amount / months).quantize(Decimal("0.01"))
    reply = f"If you save {_money(monthly)} per month, you could reach {_money(amount)} in {months} months."
    if assumed_default:
        reply += (
            f" (Assuming a {months}-month timeframe — tell me a different number of months "
            "if you had one in mind.)"
        )
    return reply


def _afford_reply(text: str, profile) -> str:
    amount = _extract_amount(text)
    if amount is None:
        return 'How much are you thinking of spending? For example: "Can I afford R500 on clothes?"'

    budget = _current_budget(profile)
    if budget is None:
        return _NO_BUDGET_REPLY

    category = _match_category(text, budget.categories.all())
    if category:
        remaining = category.allocated_amount - _category_spent(category)
        scope = f'your "{category.name}" budget'
    else:
        remaining = budget.total_allocated - _total_spent(budget)
        scope = "your budget"

    if amount <= remaining:
        after = remaining - amount
        return (
            f"Yes — based on {scope} you have {_money(remaining)} remaining this month. "
            f"A {_money(amount)} purchase would leave you with about {_money(after)}."
        )
    short_by = amount - remaining
    return (
        f"That would be tight — based on {scope} you only have {_money(remaining)} remaining "
        f"this month, which is {_money(short_by)} short of {_money(amount)}."
    )


def _why_increase_reply(profile) -> str:
    budget = _current_budget(profile)
    if budget is None:
        return _NO_BUDGET_REPLY

    prev_year, prev_month = _shift_month(budget.year, budget.month, -1)
    prev_budget = _budget_for(profile, prev_year, prev_month)
    if prev_budget is None:
        return (
            "I don't have last month's budget to compare against, so I can't tell you "
            "whether this month is higher."
        )

    current_total = _total_spent(budget)
    prev_total = _total_spent(prev_budget)
    diff = current_total - prev_total

    if diff <= 0:
        if diff == 0:
            return "You've spent about the same as last month so far."
        return f"Good news — you've actually spent {_money(-diff)} less than last month so far."

    pct = f" ({(diff / prev_total * 100):.0f}% higher)" if prev_total > 0 else ""
    reply = f"Your spending is up {_money(diff)}{pct} compared to last month so far."

    prev_by_name = {c.name.lower(): _category_spent(c) for c in prev_budget.categories.all()}
    best_category, best_delta, best_cur, best_prev = None, Decimal("0"), Decimal("0"), Decimal("0")
    for category in budget.categories.all():
        cur_spent = _category_spent(category)
        prev_spent = prev_by_name.get(category.name.lower(), Decimal("0"))
        delta = cur_spent - prev_spent
        if delta > best_delta:
            best_category, best_delta, best_cur, best_prev = category, delta, cur_spent, prev_spent

    if best_category is not None:
        reply += (
            f' Mainly because your "{best_category.name}" spending went from '
            f"{_money(best_prev)} to {_money(best_cur)}."
        )
    return reply


def _overspend_reply(profile) -> str:  # pylint: disable=too-many-locals
    budget = _current_budget(profile)
    if budget is None:
        return _NO_BUDGET_REPLY

    categories = list(budget.categories.all())
    if not categories:
        return "You don't have any categories set up in this month's budget yet."

    over_budget = None
    over_pct = Decimal("0")
    closest = None
    closest_ratio = Decimal("0")
    any_spend = False

    for category in categories:
        spent = _category_spent(category)
        if spent > 0:
            any_spend = True
        allocated = category.allocated_amount
        if allocated <= 0:
            continue
        ratio = spent / allocated
        if ratio > 1 and (over_budget is None or ratio > over_pct):
            over_budget, over_pct = category, ratio
        if closest is None or ratio > closest_ratio:
            closest, closest_ratio = category, ratio

    if not any_spend:
        return "You haven't logged any spending yet this month, so there's nothing to flag."

    if over_budget is not None:
        spent = _category_spent(over_budget)
        pct_over = (over_pct - 1) * 100
        return (
            f'Your highest overspend is "{over_budget.name}": you\'ve spent {_money(spent)} this month, '
            f"which is {pct_over:.0f}% over your {_money(over_budget.allocated_amount)} budget for it."
        )

    if closest is not None:
        spent = _category_spent(closest)
        return (
            f"Nothing's over budget yet — your closest category is \"{closest.name}\" at "
            f"{(closest_ratio * 100):.0f}% of its {_money(closest.allocated_amount)} allocation."
        )
    return "You haven't logged any spending yet this month, so there's nothing to flag."


def _search_reply(text: str, profile) -> str:
    budget = _current_budget(profile)
    if budget is None:
        return _NO_BUDGET_REPLY

    queryset = Transaction.objects.filter(category__budget=budget).select_related("category")
    threshold = _extract_threshold(text)
    if threshold:
        direction, amount = threshold
        queryset = queryset.filter(**{f"amount__{direction}": amount})

    category = _match_category(text, budget.categories.all())
    if category:
        queryset = queryset.filter(category=category)

    transactions = list(queryset.order_by("-purchase_date")[:SEARCH_RESULT_LIMIT])
    if not transactions:
        return "I couldn't find any matching transactions this month."

    lines = []
    for txn in transactions:
        label = txn.description or txn.category.name
        lines.append(f"• {txn.purchase_date:%d %b}: {_money(txn.amount)} — {label}")
    return "Here's what I found:\n" + "\n".join(lines)


def _budget_status_reply(profile) -> str:
    budget = _current_budget(profile)
    if budget is None:
        return _NO_BUDGET_REPLY

    spent = _total_spent(budget)
    remaining = budget.total_allocated - spent
    pct_used = (spent / budget.total_allocated * 100) if budget.total_allocated > 0 else Decimal("0")
    return (
        f"You've spent {_money(spent)} of your {_money(budget.total_allocated)} budget this month "
        f"({pct_used:.0f}% used), leaving {_money(remaining)}."
    )


def _spend_by_category_reply(text: str, profile) -> str:
    budget = _current_budget(profile)
    if budget is None:
        return _NO_BUDGET_REPLY

    total = _total_spent(budget)
    category = _match_category(text, budget.categories.all())
    if category is None:
        return f"You've spent {_money(total)} in total this month across all categories."

    spent = _category_spent(category)
    pct = (spent / total * 100) if total > 0 else Decimal("0")
    return (
        f"You've spent {_money(spent)} on {category.name} this month, "
        f"which is {pct:.0f}% of your total spending."
    )
