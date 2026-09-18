import { useEffect, useState } from "react";

import { api } from "../api/client.js";
import { useCart } from "../context/CartContext.jsx";

// Rule 5's cold-start fallback surfaced in the UI: cheap picks in whatever
// categories the student already spends on (or every category, for a
// brand-new student — see apps/recommendations/engine.py). Renders nothing
// once there's nothing left to show, rather than an empty card.
export default function RecommendationsWidget() {
  const { addItem } = useCart();
  const [recommendations, setRecommendations] = useState(null);
  const [busyId, setBusyId] = useState(null);

  useEffect(() => {
    api
      .get("/recommendations/")
      .then(({ data }) => setRecommendations(data.results))
      .catch(() => setRecommendations([]));
  }, []);

  async function dismiss(recommendationId) {
    setBusyId(recommendationId);
    try {
      await api.post(`/recommendations/${recommendationId}/feedback/`, { was_accepted: false });
      setRecommendations((prev) => prev.filter((r) => r.recommendation_id !== recommendationId));
    } catch {
      setBusyId(null);
    }
  }

  async function addToCart(recommendation) {
    if (!recommendation.offer) return;
    setBusyId(recommendation.recommendation_id);
    try {
      await addItem(recommendation.product_id, recommendation.offer.retailer_id, 1);
      await api.post(`/recommendations/${recommendation.recommendation_id}/feedback/`, {
        was_accepted: true,
      });
      setRecommendations((prev) =>
        prev.filter((r) => r.recommendation_id !== recommendation.recommendation_id)
      );
    } catch {
      setBusyId(null);
    }
  }

  if (!recommendations || recommendations.length === 0) return null;

  return (
    <div className="mt-5 rounded-2xl bg-white p-6 shadow-card dark:bg-navy-900">
      <h2 className="font-semibold text-slate-900 dark:text-white">Recommended for you</h2>
      <p className="text-sm text-slate-500 dark:text-slate-400">
        Cheap picks in the categories you spend on.
      </p>
      <div className="mt-4 space-y-3">
        {recommendations.slice(0, 3).map((r) => (
          <div
            key={r.recommendation_id}
            className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-100 p-3 dark:border-navy-800"
          >
            <div>
              <p className="font-medium text-slate-900 dark:text-white">{r.product_name}</p>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {r.offer
                  ? `R${Number(r.offer.total_landed_cost).toFixed(2)} at ${r.offer.retailer_name}`
                  : "No current offer"}
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => addToCart(r)}
                disabled={busyId === r.recommendation_id || !r.offer}
                className="rounded-lg bg-brand-600 px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-brand-700 disabled:opacity-50"
              >
                Add to cart
              </button>
              <button
                onClick={() => dismiss(r.recommendation_id)}
                disabled={busyId === r.recommendation_id}
                className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 transition-colors hover:bg-slate-50 disabled:opacity-50 dark:border-navy-700 dark:text-slate-300 dark:hover:bg-navy-800"
              >
                Not interested
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
