import { useEffect, useRef, useState } from "react";

import { api } from "../api/client.js";
import { IconCart, IconPin, IconSearch } from "../components/icons.jsx";
import { useCart } from "../context/CartContext.jsx";

const SORT_OPTIONS = [
  { value: "landed_cost_asc", label: "Price: Low to High" },
  { value: "landed_cost_desc", label: "Price: High to Low" },
];
const SUGGESTION_DEBOUNCE_MS = 250;
const DEFAULT_RADIUS_KM = 25;

function formatDistance(km) {
  if (km === null || km === undefined) return "Online only";
  return `${Number(km).toFixed(1)} km away`;
}

export default function Search() {
  const { addItem } = useCart();

  const [q, setQ] = useState("");
  const [color, setColor] = useState("");
  const [size, setSize] = useState("");
  const [sort, setSort] = useState("landed_cost_asc");
  const [radiusKm, setRadiusKm] = useState(DEFAULT_RADIUS_KM);

  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const suggestionTimer = useRef(null);

  // "near me" — real browser geolocation, opt-in. Falls back to the
  // student's campus (handled server-side) when not granted/available.
  // The radius filter only applies once real coordinates are in — a
  // campus-based guess is too approximate to fairly exclude anything.
  const [coords, setCoords] = useState(null); // {lat, lon} | null
  const [locationStatus, setLocationStatus] = useState("idle"); // idle | locating | granted | denied

  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [addedKeys, setAddedKeys] = useState(new Set());

  async function runSearch(e) {
    e?.preventDefault();
    setShowSuggestions(false);
    setLoading(true);
    setError("");
    try {
      const { data } = await api.get("/catalog/search/", {
        params: {
          q: q || undefined,
          color: color || undefined,
          size: size || undefined,
          sort,
          lat: coords?.lat,
          lon: coords?.lon,
          radius_km: coords ? radiusKm : undefined,
        },
      });
      setResults(data.results);
    } catch {
      setError("Could not load search results. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  // Re-run whenever sort, location, or the radius change — those are all
  // controls, not free text, so there's no reason to wait for a manual
  // submit. The name/colour/size fields only apply on submit.
  useEffect(() => {
    runSearch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sort, coords, radiusKm]);

  function handleQueryChange(value) {
    setQ(value);
    clearTimeout(suggestionTimer.current);

    if (value.trim().length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    suggestionTimer.current = setTimeout(async () => {
      try {
        const { data } = await api.get("/catalog/search/suggestions/", { params: { q: value } });
        setSuggestions(data.results);
        setShowSuggestions(true);
      } catch {
        // Suggestions are a nicety — a failed lookup just means no
        // dropdown, never an error banner over the whole page.
      }
    }, SUGGESTION_DEBOUNCE_MS);
  }

  function selectSuggestion(name) {
    setQ(name);
    setShowSuggestions(false);
    setTimeout(runSearch, 0);
  }

  function useMyLocation() {
    if (!navigator.geolocation) {
      setLocationStatus("denied");
      return;
    }
    setLocationStatus("locating");
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setCoords({ lat: position.coords.latitude, lon: position.coords.longitude });
        setLocationStatus("granted");
      },
      () => setLocationStatus("denied"),
      { enableHighAccuracy: false, timeout: 8000, maximumAge: 5 * 60 * 1000 }
    );
  }

  async function handleAddToCart(result) {
    const key = `${result.product_id}-${result.retailer_id}`;
    try {
      await addItem(result.product_id, result.retailer_id);
      setAddedKeys((prev) => new Set(prev).add(key));
      setTimeout(() => {
        setAddedKeys((prev) => {
          const next = new Set(prev);
          next.delete(key);
          return next;
        });
      }, 1500);
    } catch {
      // A failed add just leaves the button as-is — no page-level error
      // for what's a secondary action on a search result.
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Compare prices</h1>
      <p className="mt-1 text-slate-500 dark:text-slate-400">
        Item price, delivery, total cost, store, and how far it is from you.
      </p>

      <form onSubmit={runSearch} className="mt-6 rounded-2xl bg-white p-5 shadow-card dark:bg-navy-900">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
          <div className="relative sm:col-span-2">
            <label htmlFor="q" className="mb-1.5 block text-sm font-semibold text-slate-700 dark:text-slate-200">
              Item name
            </label>
            <div className="relative">
              <IconSearch className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                id="q"
                value={q}
                onChange={(e) => handleQueryChange(e.target.value)}
                onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
                onBlur={() => setTimeout(() => setShowSuggestions(false), 100)}
                placeholder="e.g. toothpaste, notebook, deodorant"
                autoComplete="off"
                className="w-full rounded-lg border border-slate-200 bg-slate-50 py-2.5 pl-9 pr-3.5 text-slate-900 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-navy-700 dark:bg-navy-800 dark:text-white"
              />
            </div>
            {showSuggestions && suggestions.length > 0 && (
              <ul className="absolute z-10 mt-1 w-full overflow-hidden rounded-lg border border-slate-200 bg-white shadow-card dark:border-navy-700 dark:bg-navy-800">
                {suggestions.map((s) => (
                  <li key={s.name}>
                    <button
                      type="button"
                      onMouseDown={() => selectSuggestion(s.name)}
                      className="flex w-full items-center justify-between px-3.5 py-2 text-left text-sm text-slate-700 hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-navy-700"
                    >
                      <span>{s.name}</span>
                      <span className="text-xs text-slate-400">{s.category}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
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
          <div className="flex flex-wrap items-center gap-3">
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
              type="button"
              onClick={useMyLocation}
              disabled={locationStatus === "locating"}
              className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50 disabled:opacity-50 dark:border-navy-700 dark:text-slate-200 dark:hover:bg-navy-800"
            >
              <IconPin className="h-4 w-4" />
              {locationStatus === "granted" ? "Using your location" : "Use my location"}
            </button>

            {locationStatus === "granted" && (
              <div className="flex items-center gap-2">
                <label htmlFor="radius" className="text-sm font-semibold text-slate-700 dark:text-slate-200">
                  Within
                </label>
                <select
                  id="radius"
                  value={radiusKm}
                  onChange={(e) => setRadiusKm(Number(e.target.value))}
                  className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-navy-700 dark:bg-navy-800 dark:text-white"
                >
                  {[5, 10, 25, 50, 100].map((km) => (
                    <option key={km} value={km}>
                      {km} km
                    </option>
                  ))}
                </select>
              </div>
            )}

            {locationStatus === "denied" && (
              <span className="text-xs text-slate-500 dark:text-slate-400">
                Location unavailable — showing distance from your campus instead.
              </span>
            )}
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
              Try a different item name, a wider radius, or clear the colour/size filters.
            </p>
          </div>
        )}

        {!loading && results?.length > 0 && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {results.map((r) => {
              const key = `${r.product_id}-${r.retailer_id}`;
              const isNearby = r.distance_km !== null && r.distance_km !== undefined;
              return (
                <div key={key} className="rounded-2xl bg-white p-5 shadow-card dark:bg-navy-900">
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

                  <div className="mt-4 flex items-start justify-between gap-2">
                    <div className="flex min-w-0 items-center gap-1.5 text-sm text-slate-500 dark:text-slate-400">
                      <IconPin className="h-4 w-4 shrink-0" />
                      <span className="truncate">
                        {r.retailer_name}
                        {r.store_address ? ` · ${r.store_address}` : ""}
                      </span>
                    </div>
                    <span
                      className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-bold ${
                        isNearby
                          ? "bg-brand-50 text-brand-700 dark:bg-brand-600/20 dark:text-brand-300"
                          : "bg-slate-100 text-slate-500 dark:bg-navy-800 dark:text-slate-400"
                      }`}
                    >
                      {formatDistance(r.distance_km)}
                    </span>
                  </div>

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

                  <button
                    onClick={() => handleAddToCart(r)}
                    className={`mt-4 flex w-full items-center justify-center gap-2 rounded-lg py-2 text-sm font-semibold transition-colors ${
                      addedKeys.has(key)
                        ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300"
                        : "bg-brand-600 text-white hover:bg-brand-700"
                    }`}
                  >
                    <IconCart className="h-4 w-4" />
                    {addedKeys.has(key) ? "Added to cart" : "Add to cart"}
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
