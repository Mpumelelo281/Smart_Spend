import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Tooltip,
} from "chart.js";
import { useEffect, useState } from "react";
import { Bar } from "react-chartjs-2";

import { api } from "../api/client.js";
import { useTheme } from "../context/ThemeContext.jsx";

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

const MONTH_NAMES = Array.from({ length: 12 }, (_, i) =>
  new Date(2000, i, 1).toLocaleString("en-ZA", { month: "short" })
);

// Same two colours as the monthly Allocated/Spent chart below, reused here
// for the category breakdown so the meaning of "blue = allocated, green =
// spent" stays consistent across both charts on this page.
const ALLOCATED_COLOR = "#2f7bf6";
const SPENT_COLOR = "#10b981";

export default function History() {
  const { theme } = useTheme();
  const [budgets, setBudgets] = useState(null);
  const [error, setError] = useState("");
  const [selectedBudgetId, setSelectedBudgetId] = useState("");
  const [exporting, setExporting] = useState(false);
  const [forecast, setForecast] = useState(null);

  useEffect(() => {
    api
      .get("/budgets/")
      .then(({ data }) => {
        // GET /budgets/ is already ordered -year,-month (see
        // BudgetListCreateView.get_queryset) — reverse it here so the
        // chart reads left-to-right in chronological order.
        const results = (data.results ?? data).slice().reverse();
        setBudgets(results);
      })
      .catch(() => setError("Could not load your budget history."));
  }, []);

  async function exportExcel() {
    setExporting(true);
    try {
      // The download needs the same Bearer token every other request
      // sends (see api/client.js) — a plain <a href> can't attach that,
      // so this fetches the file as a blob and triggers the save itself.
      // A real .xlsx, not CSV: the backend formats it as a banded Excel
      // Table with a bold header (see BudgetHistoryExportView) — CSV has
      // no concept of formatting to carry that over.
      const response = await api.get("/budgets/export/", { responseType: "blob" });
      const url = URL.createObjectURL(response.data);
      const link = document.createElement("a");
      link.href = url;
      link.download = "smartspend-budget-history.xlsx";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch {
      setError("Could not export your budget history right now.");
    } finally {
      setExporting(false);
    }
  }

  useEffect(() => {
    if (!budgets || budgets.length === 0) return;
    // Mirrors the category-breakdown selection below: defaults to the most
    // recent month until the student picks a different one.
    const budget = budgets.find((b) => b.budget_id === selectedBudgetId) ?? budgets[budgets.length - 1];
    setForecast(null);
    api
      .get(`/budgets/${budget.budget_id}/forecast/`)
      .then(({ data }) => setForecast(data))
      .catch(() => setForecast(null));
  }, [budgets, selectedBudgetId]);

  if (error) {
    return <p className="text-sm font-medium text-red-600 dark:text-red-400">{error}</p>;
  }
  if (!budgets) {
    return <p className="text-slate-500 dark:text-slate-400">Loading history…</p>;
  }
  if (budgets.length === 0) {
    return (
      <div className="rounded-2xl bg-white p-8 text-center shadow-card dark:bg-navy-900">
        <p className="font-semibold text-slate-900 dark:text-white">No budgets yet</p>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Once you&apos;ve set up a budget and logged some spending, it&apos;ll show up here month by
          month.
        </p>
      </div>
    );
  }

  const isDark = theme === "dark";
  const gridColor = isDark ? "rgba(148, 163, 184, 0.15)" : "rgba(15, 23, 42, 0.08)";
  const tickColor = isDark ? "#cbd5e1" : "#475569";

  const labels = budgets.map((b) => `${MONTH_NAMES[b.month - 1]} ${b.year}`);
  const data = {
    labels,
    datasets: [
      {
        label: "Allocated",
        data: budgets.map((b) => Number(b.total_allocated)),
        backgroundColor: ALLOCATED_COLOR,
        borderRadius: 6,
        maxBarThickness: 36,
      },
      {
        label: "Spent",
        data: budgets.map((b) => Number(b.total_spent)),
        backgroundColor: SPENT_COLOR,
        borderRadius: 6,
        maxBarThickness: 36,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: tickColor } },
      tooltip: {
        callbacks: { label: (ctx) => `${ctx.dataset.label}: R${ctx.parsed.y.toFixed(2)}` },
      },
    },
    scales: {
      x: { grid: { color: gridColor }, ticks: { color: tickColor } },
      y: {
        beginAtZero: true,
        grid: { color: gridColor },
        ticks: { color: tickColor, callback: (v) => `R${v}` },
      },
    },
  };

  // Category breakdown: defaults to the most recent month (budgets is
  // chronological ascending, see the reverse() above) until the student
  // picks a different one from the dropdown.
  const selectedBudget =
    budgets.find((b) => b.budget_id === selectedBudgetId) ?? budgets[budgets.length - 1];
  const categories = selectedBudget.categories;

  const categoryLabels = categories.map((c) => c.name);
  const categoryData = {
    labels: categoryLabels,
    datasets: [
      {
        label: "Allocated",
        data: categories.map((c) => Number(c.allocated_amount)),
        backgroundColor: ALLOCATED_COLOR,
        borderRadius: 4,
        maxBarThickness: 20,
      },
      {
        label: "Spent",
        data: categories.map((c) => Number(c.spent_amount)),
        backgroundColor: SPENT_COLOR,
        borderRadius: 4,
        maxBarThickness: 20,
      },
    ],
  };

  // Horizontal bars (indexAxis: "y") read category names left-aligned
  // instead of rotated/truncated under vertical bars — the same reason
  // choosing-a-form favours a horizontal layout for part-to-whole data
  // with more than a couple of named categories.
  const categoryOptions = {
    indexAxis: "y",
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: tickColor } },
      tooltip: {
        callbacks: { label: (ctx) => `${ctx.dataset.label}: R${ctx.parsed.x.toFixed(2)}` },
      },
    },
    scales: {
      x: {
        beginAtZero: true,
        grid: { color: gridColor },
        ticks: { color: tickColor, callback: (v) => `R${v}` },
      },
      y: { grid: { display: false }, ticks: { color: tickColor } },
    },
  };

  return (
    <div>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Spending history</h1>
          <p className="mt-1 text-slate-500 dark:text-slate-400">
            Allocated vs. actually spent, month by month.
          </p>
        </div>
        <button
          onClick={exportExcel}
          disabled={exporting}
          className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-card transition-colors hover:bg-slate-50 disabled:opacity-50 dark:border-navy-700 dark:bg-navy-900 dark:text-slate-200 dark:hover:bg-navy-800"
        >
          {exporting ? "Exporting…" : "Export Excel"}
        </button>
      </div>

      {forecast && (
        <div className="mt-6 rounded-2xl bg-white p-6 shadow-card dark:bg-navy-900">
          <h2 className="font-semibold text-slate-900 dark:text-white">
            {forecast.days_elapsed >= forecast.days_in_month ? "Month summary" : "On track for"}
          </h2>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Projected from R{Number(forecast.total_spent).toFixed(2)} spent over{" "}
            {forecast.days_elapsed} of {forecast.days_in_month} days.
          </p>
          <p
            className={`mt-3 text-2xl font-extrabold ${
              forecast.will_exceed_allowance
                ? "text-red-600 dark:text-red-400"
                : "text-emerald-600 dark:text-emerald-400"
            }`}
          >
            R{Number(forecast.total_projected).toFixed(2)}{" "}
            <span className="text-sm font-medium text-slate-400">
              of R{Number(forecast.total_allocated).toFixed(2)} allocated
            </span>
          </p>
          {forecast.will_exceed_allowance && (
            <p className="mt-1 text-xs font-medium text-red-600 dark:text-red-400">
              At this pace you&apos;re on track to go over.
            </p>
          )}
        </div>
      )}

      <div className="mt-6 rounded-2xl bg-white p-6 shadow-card dark:bg-navy-900">
        <div style={{ height: 320 }}>
          <Bar data={data} options={options} />
        </div>
      </div>

      <div className="mt-6 rounded-2xl bg-white p-6 shadow-card dark:bg-navy-900">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="font-semibold text-slate-900 dark:text-white">Category breakdown</h2>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Allocated vs. spent within one month.
            </p>
          </div>
          <select
            value={selectedBudget.budget_id}
            onChange={(e) => setSelectedBudgetId(e.target.value)}
            className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-navy-700 dark:bg-navy-800 dark:text-white"
          >
            {budgets
              .slice()
              .reverse()
              .map((b) => (
                <option key={b.budget_id} value={b.budget_id}>
                  {MONTH_NAMES[b.month - 1]} {b.year}
                </option>
              ))}
          </select>
        </div>

        <div className="mt-4" style={{ height: Math.max(180, categories.length * 56) }}>
          <Bar data={categoryData} options={categoryOptions} />
        </div>

        {categories.some((c) => Number(c.spent_amount) > Number(c.allocated_amount)) && (
          <div className="mt-4 flex flex-wrap gap-x-4 gap-y-1 border-t border-slate-100 pt-4 text-xs dark:border-navy-800">
            {categories
              .filter((c) => Number(c.spent_amount) > Number(c.allocated_amount))
              .map((c) => (
                <span key={c.category_id} className="font-medium text-red-600 dark:text-red-400">
                  {c.name} is R{(Number(c.spent_amount) - Number(c.allocated_amount)).toFixed(2)} over
                </span>
              ))}
          </div>
        )}
      </div>

      <div className="mt-6 overflow-x-auto rounded-2xl bg-white shadow-card dark:bg-navy-900">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-100 text-slate-500 dark:border-navy-800 dark:text-slate-400">
              <th className="px-6 py-3 font-medium">Month</th>
              <th className="px-6 py-3 font-medium">Allocated</th>
              <th className="px-6 py-3 font-medium">Spent</th>
              <th className="px-6 py-3 font-medium">Remaining</th>
            </tr>
          </thead>
          <tbody>
            {budgets.map((b) => {
              const allocated = Number(b.total_allocated);
              const spent = Number(b.total_spent);
              const remaining = allocated - spent;
              return (
                <tr
                  key={b.budget_id}
                  className="border-b border-slate-50 last:border-0 dark:border-navy-800/60"
                >
                  <td className="px-6 py-3 font-medium text-slate-900 dark:text-white">
                    {MONTH_NAMES[b.month - 1]} {b.year}
                  </td>
                  <td className="px-6 py-3 text-slate-700 dark:text-slate-300">R{allocated.toFixed(2)}</td>
                  <td className="px-6 py-3 text-slate-700 dark:text-slate-300">R{spent.toFixed(2)}</td>
                  <td
                    className={`px-6 py-3 font-medium ${
                      remaining < 0 ? "text-red-600 dark:text-red-400" : "text-emerald-600 dark:text-emerald-400"
                    }`}
                  >
                    R{remaining.toFixed(2)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
