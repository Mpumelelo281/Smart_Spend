import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api/client.js";
import { IconChart, IconPlus, IconSearch, IconWallet } from "../components/icons.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { validateMoneyAmount, validateRequired } from "../validators.js";

const now = new Date();
const today = now.toISOString().slice(0, 10);

// Below this fraction of the allowance remaining, the dashboard treats
// the student as "running low" — matches the same 80%-spent framing as
// the backend's threshold notifications (Rule 10: BUDGET_ALERT_THRESHOLD_PCT).
const LOW_BALANCE_REMAINING_FRACTION = 0.2;

const OTHER_CATEGORY = "__other__";

function LogExpenseForm({ budget, onLogged }) {
  const [categoryId, setCategoryId] = useState(budget.categories[0]?.category_id ?? "");
  const [customCategoryName, setCustomCategoryName] = useState("");
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const isOther = categoryId === OTHER_CATEGORY;

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    const amountError = validateMoneyAmount(amount);
    const categoryError = isOther
      ? validateRequired("Category name")(customCategoryName)
      : validateRequired("Category")(categoryId);
    if (amountError || categoryError) {
      setError(amountError || categoryError);
      return;
    }

    setSubmitting(true);
    try {
      // "Other" has no BudgetCategory yet — create it on the fly (or reuse
      // one with the same name, server-side) before logging against it, so
      // spend that doesn't fit a pre-set category still has somewhere to go.
      let targetCategoryId = categoryId;
      if (isOther) {
        const { data: category } = await api.post(`/budgets/${budget.budget_id}/categories/`, {
          name: customCategoryName,
        });
        targetCategoryId = category.category_id;
      }

      await api.post("/budgets/transactions/", {
        category: targetCategoryId,
        amount,
        purchase_date: today,
        description,
      });
      setAmount("");
      setDescription("");
      setCustomCategoryName("");
      setCategoryId(budget.categories[0]?.category_id ?? "");
      await onLogged();
    } catch (err) {
      setError(err.response?.data?.amount?.[0] || "Could not log that expense. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mt-4 flex flex-wrap items-end gap-3">
      <div className="flex-1 min-w-[140px]">
        <label htmlFor="expense-category" className="mb-1 block text-xs font-semibold text-slate-500 dark:text-slate-400">
          Category
        </label>
        <select
          id="expense-category"
          value={categoryId}
          onChange={(e) => setCategoryId(e.target.value)}
          className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-navy-700 dark:bg-navy-800 dark:text-white"
        >
          {budget.categories.map((c) => (
            <option key={c.category_id} value={c.category_id}>
              {c.name}
            </option>
          ))}
          <option value={OTHER_CATEGORY}>Other</option>
        </select>
      </div>
      {isOther && (
        <div className="flex-1 min-w-[140px]">
          <label htmlFor="expense-other-name" className="mb-1 block text-xs font-semibold text-slate-500 dark:text-slate-400">
            What was it for?
          </label>
          <input
            id="expense-other-name"
            value={customCategoryName}
            onChange={(e) => setCustomCategoryName(e.target.value)}
            placeholder="e.g. Textbooks"
            className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-navy-700 dark:bg-navy-800 dark:text-white"
          />
        </div>
      )}
      <div className="w-28">
        <label htmlFor="expense-amount" className="mb-1 block text-xs font-semibold text-slate-500 dark:text-slate-400">
          Amount (R)
        </label>
        <input
          id="expense-amount"
          inputMode="decimal"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          placeholder="0.00"
          className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-navy-700 dark:bg-navy-800 dark:text-white"
        />
      </div>
      <div className="flex-1 min-w-[140px]">
        <label htmlFor="expense-desc" className="mb-1 block text-xs font-semibold text-slate-500 dark:text-slate-400">
          Description (optional)
        </label>
        <input
          id="expense-desc"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="e.g. Bread and milk"
          className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-navy-700 dark:bg-navy-800 dark:text-white"
        />
      </div>
      <button
        type="submit"
        disabled={submitting || budget.categories.length === 0}
        className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white shadow-card transition-colors hover:bg-brand-700 disabled:opacity-50"
      >
        {submitting ? "Logging…" : "Log expense"}
      </button>
      {error && (
        <p role="alert" className="w-full text-xs font-medium text-red-600 dark:text-red-400">
          {error}
        </p>
      )}
    </form>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const firstName = user?.email?.split("@")[0] ?? "there";
  const allowance = Number(user?.profile?.allowance_amount ?? 0);

  const [currentBudget, setCurrentBudget] = useState(undefined); // undefined = loading, null = none yet

  async function fetchCurrentBudget() {
    try {
      const { data } = await api.get("/budgets/");
      const budgets = data.results ?? data;
      const match = budgets.find((b) => b.month === now.getMonth() + 1 && b.year === now.getFullYear());
      setCurrentBudget(match ?? null);
    } catch {
      setCurrentBudget(null);
    }
  }

  useEffect(() => {
    fetchCurrentBudget();
  }, []);

  const spent = currentBudget ? Number(currentBudget.total_spent) : 0;
  const remaining = allowance - spent;
  const remainingFraction = allowance > 0 ? remaining / allowance : 1;
  const isLow = currentBudget && remainingFraction <= LOW_BALANCE_REMAINING_FRACTION;
  const isOver = remaining < 0;

  const heroGradient = isOver
    ? "from-red-600 to-red-900"
    : isLow
      ? "from-amber-500 to-orange-700"
      : "from-brand-600 to-navy-800";

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Hi, {firstName} 👋</h1>
      <p className="mt-1 text-slate-500 dark:text-slate-400">
        Here&apos;s where your NSFAS allowance stands this month.
      </p>

      {currentBudget && (isLow || isOver) && (
        <div
          role="alert"
          className={`mt-5 flex items-center gap-3 rounded-xl border p-4 ${
            isOver
              ? "border-red-200 bg-red-50 text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300"
              : "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-300"
          }`}
        >
          <span className="text-lg">{isOver ? "🚨" : "⚠️"}</span>
          <p className="text-sm font-medium">
            {isOver
              ? `You've gone R${Math.abs(remaining).toFixed(2)} over your R${allowance.toFixed(2)} allowance this month.`
              : `You have R${remaining.toFixed(2)} left this month — that's under 20% of your allowance.`}
          </p>
        </div>
      )}

      <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-3">
        <div className={`rounded-2xl bg-gradient-to-br p-6 text-white shadow-card ${heroGradient}`}>
          <p className="text-sm font-medium text-white/80">
            {currentBudget ? "Left this month" : "Monthly allowance"}
          </p>
          <p className="mt-2 text-3xl font-extrabold">R{(currentBudget ? remaining : allowance).toFixed(2)}</p>
          {currentBudget && (
            <p className="mt-1 text-xs text-white/70">
              R{spent.toFixed(2)} spent of R{allowance.toFixed(2)}
            </p>
          )}
        </div>

        <div className="rounded-2xl bg-white p-6 shadow-card dark:bg-navy-900">
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Campus</p>
          <p className="mt-2 text-xl font-bold text-slate-900 dark:text-white">
            {user?.profile?.campus || "—"}
          </p>
        </div>

        <div className="rounded-2xl bg-white p-6 shadow-card dark:bg-navy-900">
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Budget status</p>
          {currentBudget ? (
            <p className="mt-2 flex items-center gap-2 text-xl font-bold text-emerald-600 dark:text-emerald-400">
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
              Set up
            </p>
          ) : (
            <p className="mt-2 flex items-center gap-2 text-xl font-bold text-amber-600 dark:text-amber-400">
              <span className="h-2.5 w-2.5 rounded-full bg-amber-500" />
              Not set up
            </p>
          )}
        </div>
      </div>

      <div className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-3">
        <div className="rounded-2xl bg-white p-6 shadow-card dark:bg-navy-900 sm:col-span-2">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-600/20 dark:text-brand-300">
              <IconWallet className="h-6 w-6" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="font-semibold text-slate-900 dark:text-white">
                {currentBudget ? "Log an expense" : "Set up this month's budget"}
              </p>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                {currentBudget
                  ? "Record what you've spent so your remaining balance stays accurate."
                  : `Split your R${allowance.toFixed(2)} across food, data, toiletries, and more.`}
              </p>
            </div>
            {!currentBudget && (
              <Link
                to="/budgets/new"
                className="hidden shrink-0 items-center gap-2 rounded-lg bg-brand-600 px-4 py-2.5 font-semibold text-white shadow-card transition-colors hover:bg-brand-700 sm:flex"
              >
                <IconPlus className="h-4 w-4" />
                Create budget
              </Link>
            )}
          </div>
          {currentBudget && <LogExpenseForm budget={currentBudget} onLogged={fetchCurrentBudget} />}
        </div>

        <Link
          to="/search"
          className="flex items-center gap-4 rounded-2xl bg-white p-6 shadow-card transition-transform hover:-translate-y-0.5 dark:bg-navy-900"
        >
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-300">
            <IconSearch className="h-6 w-6" />
          </div>
          <div>
            <p className="font-semibold text-slate-900 dark:text-white">Compare prices</p>
            <p className="text-sm text-slate-500 dark:text-slate-400">Find the best deal nearby.</p>
          </div>
        </Link>
      </div>

      <Link
        to="/history"
        className="mt-5 flex items-center gap-4 rounded-2xl bg-white p-6 shadow-card transition-transform hover:-translate-y-0.5 dark:bg-navy-900"
      >
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-600/20 dark:text-brand-300">
          <IconChart className="h-6 w-6" />
        </div>
        <div>
          <p className="font-semibold text-slate-900 dark:text-white">Spending history</p>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            See how much you allocated vs. spent in previous months.
          </p>
        </div>
      </Link>
    </div>
  );
}
