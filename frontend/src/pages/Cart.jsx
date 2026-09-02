import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api/client.js";
import { IconMinus, IconPlus, IconTrash } from "../components/icons.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { useCart } from "../context/CartContext.jsx";

const now = new Date();

export default function Cart() {
  const { user } = useAuth();
  const { items, cartTotal, updateQuantity, removeItem } = useCart();
  const allowance = Number(user?.profile?.allowance_amount ?? 0);

  const [remaining, setRemaining] = useState(null);

  useEffect(() => {
    api
      .get("/budgets/")
      .then(({ data }) => {
        const budgets = data.results ?? data;
        const current = budgets.find((b) => b.month === now.getMonth() + 1 && b.year === now.getFullYear());
        setRemaining(current ? allowance - Number(current.total_spent) : allowance);
      })
      .catch(() => setRemaining(allowance));
  }, [allowance]);

  const afterCart = remaining === null ? null : remaining - cartTotal;
  const wouldOverspend = afterCart !== null && afterCart < 0;

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Your cart</h1>
      <p className="mt-1 text-slate-500 dark:text-slate-400">
        Items you&apos;re planning to buy — see how they stack up against what&apos;s left in your budget.
      </p>

      {items.length === 0 ? (
        <div className="mt-6 rounded-2xl bg-white p-8 text-center shadow-card dark:bg-navy-900">
          <p className="font-semibold text-slate-900 dark:text-white">Your cart is empty</p>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Add items from{" "}
            <Link to="/search" className="font-semibold text-brand-600 hover:underline dark:text-brand-400">
              price search
            </Link>{" "}
            to start planning.
          </p>
        </div>
      ) : (
        <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="space-y-3 lg:col-span-2">
            {items.map((item) => (
              <div
                key={item.cart_item_id}
                className="flex items-center gap-4 rounded-2xl bg-white p-4 shadow-card dark:bg-navy-900"
              >
                <div className="min-w-0 flex-1">
                  <p className="truncate font-semibold text-slate-900 dark:text-white">{item.product_name}</p>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    {item.retailer_name}
                    {item.color ? ` · ${item.color}` : ""}
                    {item.size ? ` · ${item.size}` : ""}
                  </p>
                </div>

                <div className="flex items-center gap-1.5 rounded-lg border border-slate-200 dark:border-navy-700">
                  <button
                    onClick={() => updateQuantity(item.cart_item_id, Math.max(1, item.quantity - 1))}
                    aria-label={`Decrease quantity of ${item.product_name}`}
                    className="p-2 text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
                  >
                    <IconMinus className="h-3.5 w-3.5" />
                  </button>
                  <span className="w-6 text-center text-sm font-semibold text-slate-900 dark:text-white">
                    {item.quantity}
                  </span>
                  <button
                    onClick={() => updateQuantity(item.cart_item_id, item.quantity + 1)}
                    aria-label={`Increase quantity of ${item.product_name}`}
                    className="p-2 text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
                  >
                    <IconPlus className="h-3.5 w-3.5" />
                  </button>
                </div>

                <p className="w-24 shrink-0 text-right font-bold text-slate-900 dark:text-white">
                  R{Number(item.line_total).toFixed(2)}
                </p>

                <button
                  onClick={() => removeItem(item.cart_item_id)}
                  aria-label={`Remove ${item.product_name} from cart`}
                  className="shrink-0 rounded-lg p-2 text-red-500 transition-colors hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950/40"
                >
                  <IconTrash className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>

          <div className="h-fit rounded-2xl bg-white p-6 shadow-card dark:bg-navy-900">
            <h2 className="font-semibold text-slate-900 dark:text-white">Summary</h2>
            <div className="mt-4 flex items-baseline justify-between text-sm">
              <span className="text-slate-500 dark:text-slate-400">Cart total</span>
              <span className="font-bold text-slate-900 dark:text-white">R{cartTotal.toFixed(2)}</span>
            </div>
            {remaining !== null && (
              <>
                <div className="mt-2 flex items-baseline justify-between text-sm">
                  <span className="text-slate-500 dark:text-slate-400">Left in budget</span>
                  <span className="font-medium text-slate-700 dark:text-slate-300">R{remaining.toFixed(2)}</span>
                </div>
                <div className="mt-3 border-t border-slate-100 pt-3 dark:border-navy-800">
                  <div className="flex items-baseline justify-between">
                    <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">
                      {wouldOverspend ? "Over budget by" : "Left after this cart"}
                    </span>
                    <span
                      className={`text-lg font-extrabold ${
                        wouldOverspend
                          ? "text-red-600 dark:text-red-400"
                          : "text-emerald-600 dark:text-emerald-400"
                      }`}
                    >
                      R{Math.abs(afterCart).toFixed(2)}
                    </span>
                  </div>
                  {wouldOverspend && (
                    <p className="mt-2 text-xs text-red-600 dark:text-red-400">
                      Buying everything in this cart would put you over your remaining budget.
                    </p>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
