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

export default function History() {
  const { theme } = useTheme();
  const [budgets, setBudgets] = useState(null);
  const [error, setError] = useState("");

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
        backgroundColor: "#2f7bf6",
        borderRadius: 6,
        maxBarThickness: 36,
      },
      {
        label: "Spent",
        data: budgets.map((b) => Number(b.total_spent)),
        backgroundColor: "#10b981",
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

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Spending history</h1>
      <p className="mt-1 text-slate-500 dark:text-slate-400">
        Allocated vs. actually spent, month by month.
      </p>

      <div className="mt-6 rounded-2xl bg-white p-6 shadow-card dark:bg-navy-900">
        <div style={{ height: 320 }}>
          <Bar data={data} options={options} />
        </div>
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
