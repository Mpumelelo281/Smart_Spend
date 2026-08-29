/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Matches the reference wireframes: a dark navy sidebar against a
        // light, card-based content area, blue primary actions, green for
        // confirm/save, amber/red for alert priority badges.
        navy: {
          950: "#0b1a2e",
          900: "#0f2543",
          800: "#15335c",
          700: "#1d4573",
        },
        brand: {
          50: "#eff6ff",
          100: "#dbeafe",
          500: "#2f7bf6",
          600: "#2563eb",
          700: "#1d4ed8",
        },
      },
      boxShadow: {
        card: "0 1px 2px 0 rgb(15 23 42 / 0.06), 0 1px 3px 0 rgb(15 23 42 / 0.08)",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
