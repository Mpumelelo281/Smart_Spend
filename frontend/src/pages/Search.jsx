import { useEffect, useState } from "react";

import { api } from "../api/client.js";
import { IconPin, IconSearch } from "../components/icons.jsx";

const SORT_OPTIONS = [
  { value: "landed_cost_asc", label: "Price: Low to High" },
  { value: "landed_cost_desc", label: "Price: High to Low" },
];

function formatDistance(km) {
  if (km === null || km === undefined) return "Online only";
  return `${km} km away`;
}

export default function Search() {
  const [q, setQ] = useState("");
  const [color, setColor] = useState("");
  const [size, setSize] = useState("");
  const [sort, setSort] = useState("landed_cost_asc");

  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function runSearch(e) {
    e?.preventDefault();
    setLoading(true);
    setError("");
    try {
      const { data } = await api.get("/catalog/search/", {
        params: {
          q: q || undefined,
          color: color || undefined,
          size: size || undefined,
          sort,
        },
      });
      setResults(data.results);
    } catch {
      setError("Could not load search results. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  // Load the full catalogue once on mount, then re-run whenever the sort
  // changes (filters/query only apply when the student submits the form).
  useEffect(() => {
    runSearch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sort]);

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Compare prices</h1>
      <p className="mt-1 text-slate-500 dark:text-slate-400">
        Item price, delivery, total cost, store, and how far it is from {"your campus"}.
      </p>

      <form
        onSubmit={runSearch}
        className="mt-6 rounded-2xl bg-white p-5 shadow-card dark:bg-navy-900"
      >
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
          <div className="sm:col-span-2">
            <label htmlFor="q" className="mb-1.5 block text-sm font-semibold text-slate-700 dark:text-slate-200">
              Item name
            </label>
            <div className="relative">
              <IconSearch className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                id="q"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="e.g. toothpaste, notebook, deodorant"
                className="w-full rounded-lg border border-slate-200 bg-slate-50 py-2.5 pl-9 pr-3.5 text-slate-900 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-navy-700 dark:bg-navy-800 dark:text-white"
              />
            </div>
          </div>

          <div>
            <label htmlFor="color" className="mb-1.5 block text-sm font-semibold text-slate-700 dark:text-slate-200">
              Colour
            </label>
            <input
              id="color"
              value={color}
              onChange={(e) => setColor(e.target.value)}
              placeholder="e.g. Black"
              className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-slate-900 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-navy-700 dark:bg-navy-800 dark:text-white"
            />
          </div>

          <div>
            <label htmlFor="size" className="mb-1.5 block text-sm font-semibold text-slate-700 dark:text-slate-200">
              Size
            </label>
            <input
              id="size"
              value={size}
              onChange={(e) => setSize(e.target.value)}
              placeholder="e.g. M, 500ml"
              className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-slate-900 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-navy-700 dark:bg-navy-800 dark:text-white"
            />
          </div>
        </div>

        <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <label htmlFor="sort" className="text-sm font-semibold text-slate-700 dark:text-slate-200">
              Sort
            </label>
            <select
              id="sort"
              value={sort}
              onChange={(e) => setSort(e.target.value)}
              className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-navy-700 dark:bg-navy-800 dark:text-white"
            >
              {SORT_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
          <button
            type="submit"
            className="rounded-lg bg-brand-600 px-5 py-2 text-sm font-semibold text-white shadow-card transition-colors hover:bg-brand-700"
          >
            Search
          </button>
        </div>
      </form>

      <div className="mt-6">
        {loading && <p className="text-slate-500 dark:text-slate-400">Searching…</p>}
        {error && <p className="text-sm font-medium text-red-600 dark:text-red-400">{error}</p>}
        {!loading && !error && results?.length === 0 && (
          <div className="rounded-2xl bg-white p-8 text-center shadow-card dark:bg-navy-900">
            <p className="font-semibold text-slate-900 dark:text-white">No matches</p>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Try a different item name, or clear the colour/size filters.
            </p>
          </div>
        )}

        {!loading && results?.length > 0 && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {results.map((r) => (
              <div key={`${r.product_id}-${r.retailer_id}`} className="rounded-2xl bg-white p-5 shadow-card dark:bg-navy-900">
                <p className="font-semibold text-slate-900 dark:text-white">{r.name}</p>
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600 dark:bg-navy-800 dark:text-slate-300">
                    {r.category}
                  </span>
                  {r.color && (
                    <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600 dark:bg-navy-800 dark:text-slate-300">
                      {r.color}
                    </span>
                  )}
                  {r.size && (
                    <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600 dark:bg-navy-800 dark:text-slate-300">
                      {r.size}
                    </span>
                  )}
                </div>

                <div className="mt-4 flex items-center gap-1.5 text-sm text-slate-500 dark:text-slate-400">
                  <IconPin className="h-4 w-4 shrink-0" />
                  <span className="truncate">
                    {r.retailer_name}
                    {r.store_address ? ` · ${r.store_address}` : ""}
                  </span>
                </div>
                <p className="mt-1 text-sm font-medium text-brand-600 dark:text-brand-400">
                  {formatDistance(r.distance_km)}
                </p>

                <div className="mt-4 border-t border-slate-100 pt-4 dark:border-navy-800">
                  <div className="flex items-baseline justify-between text-sm text-slate-500 dark:text-slate-400">
                    <span>Item price</span>
                    <span>R{Number(r.price).toFixed(2)}</span>
                  </div>
                  <div className="flex items-baseline justify-between text-sm text-slate-500 dark:text-slate-400">
                    <span>Delivery</span>
                    <span>R{Number(r.delivery_cost).toFixed(2)}</span>
                  </div>
                  <div className="mt-1.5 flex items-baseline justify-between">
                    <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">Total</span>
                    <span className="text-lg font-extrabold text-slate-900 dark:text-white">
                      R{Number(r.total_landed_cost).toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
