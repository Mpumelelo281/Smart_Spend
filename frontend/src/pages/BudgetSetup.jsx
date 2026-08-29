import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../api/client.js";
import FormField from "../components/FormField.jsx";
import { IconPlus, IconTrash } from "../components/icons.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { validateMoneyAmount, validateRequired, totalAllocated } from "../validators.js";

const now = new Date();

function emptyCategory() {
  return { key: crypto.randomUUID(), name: "", allocated_amount: "" };
}

export default function BudgetSetup() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const allowance = Number(user?.profile?.allowance_amount ?? 1650);

  const [month, setMonth] = useState(String(now.getMonth() + 1));
  const [year] = useState(now.getFullYear());
  const [categories, setCategories] = useState([
    { key: crypto.randomUUID(), name: "Food", allocated_amount: "" },
    { key: crypto.randomUUID(), name: "Data", allocated_amount: "" },
    { key: crypto.randomUUID(), name: "Toiletries", allocated_amount: "" },
  ]);
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const total = totalAllocated(categories);
  // Rule 1's client-side preview only — the server re-validates this exact
  // comparison against the real allowance and is what actually enforces it.
  const overAllowance = total > allowance;

  function updateCategory(key, field, value) {
    setCategories((prev) => prev.map((c) => (c.key === key ? { ...c, [field]: value } : c)));
  }

  function addCategory() {
    setCategories((prev) => [...prev, emptyCategory()]);
  }

  function removeCategory(key) {
    setCategories((prev) => prev.filter((c) => c.key !== key));
  }

  const setFieldError = (id, message) => setErrors((prev) => ({ ...prev, [id]: message }));

  async function handleSubmit(e) {
    e.preventDefault();
    setFormError("");

    const nextErrors = {};
    categories.forEach((c) => {
      nextErrors[`name-${c.key}`] = validateRequired("Category name")(c.name);
      nextErrors[`amount-${c.key}`] = validateMoneyAmount(c.allocated_amount);
    });
    setErrors(nextErrors);
    if (Object.values(nextErrors).some(Boolean) || overAllowance || categories.length === 0) {
      if (overAllowance) {
        setFormError(
          `Your categories total R${total.toFixed(2)}, which is more than your R${allowance.toFixed(2)} allowance.`
        );
      }
      return;
    }

    setSubmitting(true);
    try {
      await api.post("/budgets/", {
        month: Number(month),
        year,
        categories: categories.map((c) => ({ name: c.name, allocated_amount: c.allocated_amount })),
      });
      navigate("/", { replace: true });
    } catch (err) {
      const data = err.response?.data;
      setFormError(
        data?.categories || data?.non_field_errors || "Could not create your budget. Please try again."
      );
    } finally {
      setSubmitting(false);
    }
  }

  const pct = Math.min(100, allowance ? (total / allowance) * 100 : 0);

  return (
    <div className="mx-auto max-w-2xl pb-16">
      <h1 className="mb-1 text-2xl font-bold text-slate-900 dark:text-white">Set up this month&apos;s budget</h1>
      <p className="mb-6 text-slate-500 dark:text-slate-400">
        Your NSFAS allowance is{" "}
        <strong className="text-slate-700 dark:text-slate-200">R{allowance.toFixed(2)}</strong>. Split it
        across categories — the total can&apos;t exceed your allowance.
      </p>

      <form onSubmit={handleSubmit} noValidate className="space-y-5">
        <div className="rounded-2xl bg-white p-6 shadow-card dark:bg-navy-900">
          <label htmlFor="month" className="mb-1.5 block text-sm font-semibold text-slate-700 dark:text-slate-200">
            Month
          </label>
          <select
            id="month"
            value={month}
            onChange={(e) => setMonth(e.target.value)}
            className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-slate-900 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-navy-700 dark:bg-navy-800 dark:text-white"
          >
            {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
              <option key={m} value={m}>
                {new Date(2000, m - 1, 1).toLocaleString("en-ZA", { month: "long" })}
              </option>
            ))}
          </select>
        </div>

        <div className="rounded-2xl bg-white p-6 shadow-card dark:bg-navy-900">
          <fieldset>
            <legend className="mb-3 text-sm font-semibold text-slate-700 dark:text-slate-200">
              Categories
            </legend>
            <div className="space-y-3">
              {categories.map((c) => (
                <div
                  key={c.key}
                  className="flex items-start gap-3 rounded-xl border border-slate-100 bg-slate-50/60 p-4 dark:border-navy-800 dark:bg-navy-800/40"
                >
                  <div className="grid flex-1 grid-cols-1 gap-3 sm:grid-cols-2">
                    <FormField
                      id={`name-${c.key}`}
                      label="Name"
                      value={c.name}
                      onChange={(v) => updateCategory(c.key, "name", v)}
                      validate={validateRequired("Category name")}
                      error={errors[`name-${c.key}`]}
                      setError={setFieldError}
                    />
                    <FormField
                      id={`amount-${c.key}`}
                      label="Allocated amount (R)"
                      inputMode="decimal"
                      value={c.allocated_amount}
                      onChange={(v) => updateCategory(c.key, "allocated_amount", v)}
                      validate={validateMoneyAmount}
                      error={errors[`amount-${c.key}`]}
                      setError={setFieldError}
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => removeCategory(c.key)}
                    aria-label={`Remove ${c.name || "category"}`}
                    className="mt-6 rounded-lg p-2 text-red-500 transition-colors hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950/40"
                  >
                    <IconTrash className="h-5 w-5" />
                  </button>
                </div>
              ))}
            </div>
            <button
              type="button"
              onClick={addCategory}
              className="mt-4 flex items-center gap-1.5 rounded-lg border border-dashed border-brand-300 px-3.5 py-2 text-sm font-semibold text-brand-600 transition-colors hover:bg-brand-50 dark:border-brand-600/50 dark:text-brand-400 dark:hover:bg-brand-600/10"
            >
              <IconPlus className="h-4 w-4" />
              Add category
            </button>
          </fieldset>
        </div>

        <div className="rounded-2xl bg-white p-6 shadow-card dark:bg-navy-900">
          <div className="mb-2 flex items-center justify-between text-sm">
            <span className="font-semibold text-slate-700 dark:text-slate-200">Total allocated</span>
            <span
              className={`font-bold ${overAllowance ? "text-red-600 dark:text-red-400" : "text-slate-900 dark:text-white"}`}
              aria-live="polite"
            >
              R{total.toFixed(2)} / R{allowance.toFixed(2)}
            </span>
          </div>
          <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-navy-800">
            <div
              className={`h-full rounded-full transition-all ${overAllowance ? "bg-red-500" : "bg-emerald-500"}`}
              style={{ width: `${pct}%` }}
            />
          </div>

          {formError && (
            <p role="alert" className="mt-4 text-sm font-medium text-red-600">
              {formError}
            </p>
          )}

          <button
            type="submit"
            disabled={submitting || overAllowance}
            className="mt-5 w-full rounded-lg bg-brand-600 py-2.5 font-semibold text-white shadow-card transition-colors hover:bg-brand-700 disabled:opacity-50"
          >
            {submitting ? "Saving…" : "Create budget"}
          </button>
        </div>
      </form>
    </div>
  );
}
