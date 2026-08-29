import { useTheme } from "../context/ThemeContext.jsx";
import { IconMoon, IconSun } from "./icons.jsx";

// Shared frame for the three pre-login screens (Login, Register,
// VerifyEmail): a soft brand-gradient background behind a white card,
// echoing the sidebar's navy/blue brand mark without needing the sidebar
// itself (there's no session yet to navigate from).
export default function AuthShell({ title, subtitle, children }) {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-gradient-to-br from-navy-950 via-navy-800 to-brand-600 px-4 py-12">
      <button
        onClick={toggleTheme}
        aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
        title={isDark ? "Switch to light mode" : "Switch to dark mode"}
        className="absolute right-5 top-5 flex h-9 w-9 items-center justify-center rounded-full text-white/80 transition-colors hover:bg-white/10"
      >
        {isDark ? <IconSun className="h-5 w-5" /> : <IconMoon className="h-5 w-5" />}
      </button>

      <div className="w-full max-w-md">
        <div className="mb-6 flex items-center justify-center gap-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white font-extrabold text-brand-600 shadow-card">
            S
          </div>
          <span className="text-xl font-extrabold tracking-tight text-white">SmartSpend</span>
        </div>

        <div className="rounded-2xl bg-white p-8 shadow-card dark:bg-navy-900">
          <h1 className="mb-1 text-xl font-bold text-slate-900 dark:text-white">{title}</h1>
          {subtitle && <p className="mb-6 text-sm text-slate-500 dark:text-slate-400">{subtitle}</p>}
          {!subtitle && <div className="mb-6" />}
          {children}
        </div>
      </div>
    </div>
  );
}
