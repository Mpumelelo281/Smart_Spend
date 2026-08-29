import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import { VitePWA } from "vite-plugin-pwa";

// Progressive Web App per the mandated stack: service worker caches the
// app shell and the student's current budget so the dashboard still opens
// on a train with no signal — mobile data is expensive for this user base,
// so "no network" has to degrade to "stale but usable", never to a blank
// screen.
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["favicon.svg"],
      manifest: {
        name: "SmartSpend",
        short_name: "SmartSpend",
        description: "Budgeting and price comparison for NSFAS-funded students.",
        theme_color: "#0f2543",
        background_color: "#f1f5f9",
        display: "standalone",
        start_url: "/",
        // TODO(design): drop real 192x192 / 512x512 PNG icons into
        // public/icons/ before shipping — installability needs them, but
        // no placeholder binary belongs in the repo.
        icons: [],
      },
      workbox: {
        // NavigateFallback + runtime caching keeps the shell and the most
        // recent GET /budgets response available offline; nothing that
        // creates/mutates data is ever served from cache.
        navigateFallback: "/index.html",
        runtimeCaching: [
          {
            urlPattern: /\/api\/v1\/budgets\/?$/,
            method: "GET",
            handler: "NetworkFirst",
            options: {
              cacheName: "smartspend-budget-cache",
              networkTimeoutSeconds: 4,
              expiration: { maxEntries: 5, maxAgeSeconds: 60 * 60 * 24 },
            },
          },
        ],
      },
    }),
  ],
  server: {
    port: 5173,
  },
});
