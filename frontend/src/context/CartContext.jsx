import { createContext, useCallback, useContext, useEffect, useState } from "react";

import { api } from "../api/client.js";
import { useAuth } from "./AuthContext.jsx";

const CartContext = createContext(null);

export function CartProvider({ children }) {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [cartTotal, setCartTotal] = useState(0);

  const refresh = useCallback(async () => {
    if (!user) {
      setItems([]);
      setCartTotal(0);
      return;
    }
    try {
      const { data } = await api.get("/catalog/cart/");
      setItems(data.results);
      setCartTotal(Number(data.cart_total));
    } catch {
      // Leave whatever was already loaded rather than clearing the
      // badge/cart on a transient network blip.
    }
  }, [user]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function addItem(productId, retailerId, quantity = 1) {
    await api.post("/catalog/cart/", { product_id: productId, retailer_id: retailerId, quantity });
    await refresh();
  }

  async function updateQuantity(cartItemId, quantity) {
    await api.patch(`/catalog/cart/${cartItemId}/`, { quantity });
    await refresh();
  }

  async function removeItem(cartItemId) {
    await api.delete(`/catalog/cart/${cartItemId}/`);
    await refresh();
  }

  const itemCount = items.reduce((sum, item) => sum + item.quantity, 0);

  return (
    <CartContext.Provider
      value={{ items, cartTotal, itemCount, refresh, addItem, updateQuantity, removeItem }}
    >
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error("useCart must be used inside <CartProvider>.");
  return ctx;
}
