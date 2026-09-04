import { Link } from "react-router-dom";

import AuthSlideshow from "./AuthSlideshow.jsx";
import { IconChart, IconMoon, IconShield, IconSun, IconTarget } from "./icons.jsx";
import Logo from "./Logo.jsx";
import PhoneMockup from "./PhoneMockup.jsx";
import { useTheme } from "../context/ThemeContext.jsx";

const FEATURES = [
  { icon: IconShield, title: "Secure", text: "Your data is protected with industry-standard security." },
  { icon: IconChart, title: "Insightful", text: "Get clear insights and make smarter financial decisions." },
  { icon: IconTarget, title: "Goal Oriented", text: "Set goals and track progress to financial freedom." },
];

function ThemePillToggle() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";
  return (
    <div className="flex items-center gap-0.5 rounded-full bg-slate-100 p-1 dark:bg-navy-800">
      <button
        onClick={() => isDark && toggleTheme()}
        aria-label="Light mode"
        aria-pressed={!isDark}
        className={`flex h-7 w-7 items-center justify-center rounded-full transition-colors ${
          !isDark ? "bg-white text-amber-500 shadow-sm" : "text-slate-400 hover:text-slate-300"
        }`}
      >
        <IconSun className="h-4 w-4" />
      </button>
      <button
        onClick={() => !isDark && toggleTheme()}
        aria-label="Dark mode"
        aria-pressed={isDark}
        className={`flex h-7 w-7 items-center justify-center rounded-full transition-colors ${
          isDark ? "bg-navy-950 text-brand-400 shadow-sm" : "text-slate-400 hover:text-slate-500"
        }`}
      >
        <IconMoon className="h-4 w-4" />
      </button>
    </div>
  );
}

// Full-viewport split layout: dark-green branding panel + white form panel,
// each stretching the full window height (no floating card, no page margin
// around it). `title` is used as a React key on the form content so
// switching between Login's steps (credentials -> MFA setup -> MFA verify)
// replays the entrance animation instead of just swapping content instantly.
export default function AuthShell({ title, subtitle, children }) {
  return (
    <div className="grid min-h-screen w-full bg-white dark:bg-navy-900 lg:grid-cols-2">
      {/* Branding panel — desktop only */}
      <div className="relative hidden flex-col overflow-hidden bg-gradient-to-br from-forest-950 via-forest-900 to-forest-700 px-10 py-10 lg:flex xl:px-14 xl:py-14">
        <AuthSlideshow className="opacity-[0.12] mix-blend-luminosity" />
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -left-20 -top-20 h-72 w-72 animate-blob rounded-full bg-brand-400/20 blur-3xl"
        />
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -bottom-24 -right-10 h-80 w-80 animate-blob-slow rounded-full bg-emerald-500/10 blur-3xl"
        />

        <Logo size={34} variant="light" tagline="Spend smart. Live better." className="relative animate-fade-in-up" />

        <div className="relative mt-8">
          <h2
            className="animate-fade-in-up text-[28px] font-extrabold leading-tight text-white"
            style={{ animationDelay: "80ms" }}
          >
            Take control of <br />
            your money, <span className="text-brand-400">achieve</span> your{" "}
            <span className="text-brand-400">goals.</span>
          </h2>
          <span
            className="mt-3 block h-1 w-14 animate-fade-in-up rounded-full bg-brand-500"
            style={{ animationDelay: "140ms" }}
          />
          <p
            className="mt-4 max-w-xs animate-fade-in-up text-sm text-white/75"
            style={{ animationDelay: "180ms" }}
          >
            SmartSpend helps you budget, track expenses and reach your financial goals with
            confidence.
          </p>
        </div>

        <div
          className="relative mt-6 mb-4 flex flex-1 items-center justify-center lg:mb-6 xl:mb-10 2xl:mb-16 animate-fade-in-up"
          style={{ animationDelay: "260ms" }}
        >
          <PhoneMockup />
        </div>

        <div className="relative grid grid-cols-3 gap-3">
          {FEATURES.map(({ icon: Icon, title: t, text }, i) => (
            <div
              key={t}
              className="animate-fade-in-up rounded-xl bg-white/5 p-3 ring-1 ring-white/10 backdrop-blur-sm"
              style={{ animationDelay: `${320 + i * 90}ms` }}
            >
              <Icon className="h-4 w-4 text-brand-400" />
              <p className="mt-1.5 text-xs font-semibold text-white">{t}</p>
              <p className="mt-0.5 text-[10px] leading-snug text-white/60">{text}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Form panel */}
      <div className="relative flex min-h-screen flex-col px-6 py-8 sm:px-10 lg:px-16">
        <div className="flex items-center justify-between">
          <Logo size={30} className="lg:hidden" />
          <div className="ml-auto flex items-center gap-4">
            <ThemePillToggle />
          </div>
        </div>

        <div className="flex flex-1 flex-col justify-center">
          <div key={title} className="mx-auto w-full max-w-sm animate-fade-in-up">
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">{title}</h1>
            {subtitle && <p className="mt-1.5 text-sm text-slate-500 dark:text-slate-400">{subtitle}</p>}

            <div className="mt-7">{children}</div>
          </div>
        </div>

        <p className="pb-2 text-center text-xs text-slate-400 dark:text-slate-600">
          &copy; {new Date().getFullYear()} SmartSpend. All rights reserved. ·{" "}
          <Link to="/privacy" className="hover:underline">
            Privacy Policy
          </Link>
        </p>
      </div>
    </div>
  );
}
