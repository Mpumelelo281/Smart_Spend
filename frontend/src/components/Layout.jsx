import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";
import { useCart } from "../context/CartContext.jsx";
import { useTheme } from "../context/ThemeContext.jsx";
import {
  IconCart,
  IconChart,
  IconDashboard,
  IconLogout,
  IconMenu,
  IconMoon,
  IconSearch,
  IconSun,
  IconWallet,
  IconX,
} from "./icons.jsx";
import Logo from "./Logo.jsx";
import NotificationBell from "./NotificationBell.jsx";

const navItems = [
  { to: "/", label: "Dashboard", icon: IconDashboard, end: true },
  { to: "/budgets/new", label: "Budget", icon: IconWallet },
  { to: "/search", label: "Search prices", icon: IconSearch },
  { to: "/cart", label: "Cart", icon: IconCart, badge: "cart" },
  { to: "/history", label: "History", icon: IconChart },
];

function initials(email) {
  if (!email) return "?";
  return email[0].toUpperCase();
}

function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";
  return (
    <button
      onClick={toggleTheme}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      title={isDark ? "Switch to light mode" : "Switch to dark mode"}
      className="flex h-9 w-9 items-center justify-center rounded-full text-slate-500 transition-colors hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-navy-800"
    >
      {isDark ? <IconSun className="h-5 w-5" /> : <IconMoon className="h-5 w-5" />}
    </button>
  );
}

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const { itemCount } = useCart();
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    function handleEscape(e) {
      if (e.key === "Escape") setMobileOpen(false);
    }
    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, []);

  useEffect(() => {
    document.body.style.overflow = mobileOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileOpen]);

  return (
    <div className="min-h-screen bg-slate-100 dark:bg-navy-950">
      <div className="flex">
        {mobileOpen && (
          <div
            aria-hidden="true"
            onClick={() => setMobileOpen(false)}
            className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          />
        )}

        <aside
          className={`fixed inset-y-0 left-0 z-40 flex w-60 flex-col bg-gradient-to-b from-navy-900 to-navy-950 text-slate-100 transition-transform duration-200 ease-out lg:translate-x-0 ${
            mobileOpen ? "translate-x-0" : "-translate-x-full"
          }`}
        >
          <div className="flex items-center justify-between px-6 py-6">
            <Logo size={30} variant="light" />
            <button
              onClick={() => setMobileOpen(false)}
              aria-label="Close menu"
              className="text-slate-300 hover:text-white lg:hidden"
            >
              <IconX className="h-5 w-5" />
            </button>
          </div>

          <nav className="mt-4 flex-1 space-y-1 px-3">
            {navItems.map(({ to, label, icon: Icon, end, badge }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-brand-600 text-white shadow-card"
                      : "text-slate-300 hover:bg-navy-800 hover:text-white"
                  }`
                }
              >
                <Icon className="h-5 w-5" />
                <span className="flex-1">{label}</span>
                {badge === "cart" && itemCount > 0 && (
                  <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-white/20 px-1.5 text-xs font-bold">
                    {itemCount}
                  </span>
                )}
              </NavLink>
            ))}
          </nav>

          <div className="border-t border-navy-800 px-3 py-4">
            <button
              onClick={logout}
              className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-300 transition-colors hover:bg-navy-800 hover:text-white"
            >
              <IconLogout className="h-5 w-5" />
              Log out
            </button>
          </div>
        </aside>

        <div className="flex min-h-screen flex-1 flex-col lg:ml-60">
          <header className="flex h-16 items-center border-b border-slate-200 bg-white px-4 dark:border-navy-800 dark:bg-navy-900 lg:px-8">
            <button
              onClick={() => setMobileOpen(true)}
              aria-label="Open menu"
              className="flex h-9 w-9 items-center justify-center rounded-full text-slate-500 transition-colors hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-navy-800 lg:hidden"
            >
              <IconMenu className="h-5 w-5" />
            </button>
            <Logo size={26} className="ml-2 lg:hidden" />

            <div className="ml-auto flex items-center gap-3">
              <NotificationBell />
              <ThemeToggle />
              <NavLink
                to="/profile"
                title="Profile & security"
                className="flex items-center gap-2 rounded-full py-1 pl-1 pr-2 transition-colors hover:bg-slate-100 dark:hover:bg-navy-800"
              >
                <span className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-100 font-semibold text-brand-700 dark:bg-brand-600/20 dark:text-brand-300">
                  {initials(user?.email)}
                </span>
                <span className="hidden text-sm text-slate-500 dark:text-slate-400 sm:inline">
                  {user?.email}
                </span>
              </NavLink>
            </div>
          </header>

          <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8 lg:py-8">{children}</main>
        </div>
      </div>
    </div>
  );
}
