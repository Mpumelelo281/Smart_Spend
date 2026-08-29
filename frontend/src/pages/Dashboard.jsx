import { Link } from "react-router-dom";

import { IconChart, IconPlus, IconSearch, IconWallet } from "../components/icons.jsx";
import { useAuth } from "../context/AuthContext.jsx";

// Placeholder landing screen for Sprint 1/2. The full spending dashboard
// (category breakdown, threshold-alert history) still grows in Sprint 3 —
// this page now links out to the History and Search pages rather than
// duplicating their content inline.
export default function Dashboard() {
  const { user } = useAuth();
  const firstName = user?.email?.split("@")[0] ?? "there";
  const allowance = Number(user?.profile?.allowance_amount ?? 0);

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Hi, {firstName} 👋</h1>
      <p className="mt-1 text-slate-500 dark:text-slate-400">
        Here&apos;s where your NSFAS allowance stands this month.
      </p>

      <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-3">
        <div className="rounded-2xl bg-gradient-to-br from-brand-600 to-navy-800 p-6 text-white shadow-card">
          <p className="text-sm font-medium text-brand-100">Monthly allowance</p>
          <p className="mt-2 text-3xl font-extrabold">R{allowance.toFixed(2)}</p>
        </div>

        <div className="rounded-2xl bg-white p-6 shadow-card dark:bg-navy-900">
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Campus</p>
          <p className="mt-2 text-xl font-bold text-slate-900 dark:text-white">
            {user?.profile?.campus || "—"}
          </p>
        </div>

        <div className="rounded-2xl bg-white p-6 shadow-card dark:bg-navy-900">
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Budget status</p>
          <p className="mt-2 flex items-center gap-2 text-xl font-bold text-amber-600 dark:text-amber-400">
            <span className="h-2.5 w-2.5 rounded-full bg-amber-500" />
            Not set up
          </p>
        </div>
      </div>

      <div className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-3">
        <div className="flex items-center justify-between gap-4 rounded-2xl bg-white p-6 shadow-card dark:bg-navy-900 sm:col-span-2">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-600/20 dark:text-brand-300">
              <IconWallet className="h-6 w-6" />
            </div>
            <div>
              <p className="font-semibold text-slate-900 dark:text-white">Set up this month&apos;s budget</p>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Split your R{allowance.toFixed(2)} across food, data, toiletries, and more.
              </p>
            </div>
          </div>
          <Link
            to="/budgets/new"
            className="hidden shrink-0 items-center gap-2 rounded-lg bg-brand-600 px-4 py-2.5 font-semibold text-white shadow-card transition-colors hover:bg-brand-700 sm:flex"
          >
            <IconPlus className="h-4 w-4" />
            Create budget
          </Link>
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
