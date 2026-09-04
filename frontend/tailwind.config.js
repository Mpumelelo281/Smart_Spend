/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Dark navy stays the app shell's structural colour (sidebar,
        // dark-mode surfaces). `brand` is the accent/interactive colour —
        // green, per the reference design — and every button/link/badge
        // already built references `brand-*` semantically, so this one
        // change re-colours the whole app consistently, not just login.
        navy: {
          950: "#0b1a2e",
          900: "#0f2543",
          800: "#15335c",
          700: "#1d4573",
        },
        brand: {
          50: "#ecfdf5",
          100: "#d1fae5",
          400: "#34d399",
          500: "#22c55e",
          600: "#16a34a",
          700: "#15803d",
        },
        // Deep green, used only for the login/register branding panel's
        // background gradient (matches the reference exactly) — kept
        // separate from `navy` so the app shell's own dark surfaces don't
        // change colour.
        forest: {
          950: "#052e1f",
          900: "#0a3f2a",
          800: "#0f5233",
          700: "#166a3f",
        },
      },
      boxShadow: {
        card: "0 1px 2px 0 rgb(15 23 42 / 0.06), 0 1px 3px 0 rgb(15 23 42 / 0.08)",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      keyframes: {
        "fade-in-up": {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "pop-in": {
          "0%": { opacity: "0", transform: "scale(0.85)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        blob: {
          "0%, 100%": { transform: "translate(0, 0) scale(1)" },
          "33%": { transform: "translate(4%, -6%) scale(1.08)" },
          "66%": { transform: "translate(-3%, 4%) scale(0.96)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-10px)" },
        },
      },
      animation: {
        "fade-in-up": "fade-in-up 0.5s ease-out both",
        "fade-in": "fade-in 0.6s ease-out both",
        "pop-in": "pop-in 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) both",
        blob: "blob 14s ease-in-out infinite",
        "blob-slow": "blob 18s ease-in-out infinite reverse",
        float: "float 3.4s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
