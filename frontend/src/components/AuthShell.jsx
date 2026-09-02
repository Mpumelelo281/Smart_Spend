import { IconChart, IconMoon, IconSearch, IconSun, IconWallet } from "./icons.jsx";
import Logo from "./Logo.jsx";
import { useTheme } from "../context/ThemeContext.jsx";

const FEATURES = [
  { icon: IconWallet, text: "Split your NSFAS allowance into categories that actually hold" },
  { icon: IconSearch, text: "Compare real prices across stores before you buy" },
  { icon: IconChart, text: "See exactly where last month's allowance went" },
];

function ThemeToggle({ light }) {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";
  return (
    <button
      onClick={toggleTheme}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      title={isDark ? "Switch to light mode" : "Switch to dark mode"}
      className={`flex h-9 w-9 items-center justify-center rounded-full transition-colors ${
        light
          ? "text-white/80 hover:bg-white/10"
          : "text-slate-500 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-navy-800"
      }`}
    >
      {isDark ? <IconSun className="h-5 w-5" /> : <IconMoon className="h-5 w-5" />}
    </button>
  );
}

// Split-screen shell for the three pre-login screens (Login, Register,
// VerifyEmail): a branded panel with the logo and value proposition on
// desktop, collapsing to a single centered card on mobile. `title` is
// used as a React key on the form panel so switching between Login's
// steps (credentials -> MFA setup -> MFA verify) replays the entrance
// animation instead of just swapping content instantly.
export default function AuthShell({ title, subtitle, children }) {
  return (
    <div className="flex min-h-screen bg-white dark:bg-navy-950">
      {/* Branding panel — desktop only */}
      <div className="relative hidden w-[42%] flex-col justify-between overflow-hidden bg-gradient-to-br from-navy-950 via-navy-800 to-brand-600 px-12 py-10 lg:flex">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -left-24 -top-24 h-80 w-80 animate-blob rounded-full bg-brand-400/20 blur-3xl"
        />
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -bottom-32 -right-16 h-96 w-96 animate-blob-slow rounded-full bg-navy-700/40 blur-3xl"
        />

        <Logo size={40} variant="light" className="relative animate-fade-in-up" />

        <div className="relative">
          <h2
            className="animate-fade-in-up text-3xl font-extrabold leading-tight text-white"
            style={{ animationDelay: "80ms" }}
          >
            Make your allowance go further.
          </h2>
          <p
            className="mt-3 max-w-sm animate-fade-in-up text-brand-100"
            style={{ animationDelay: "150ms" }}
          >
            Budgeting and price comparison built for NSFAS-funded students.
          </p>
          <ul className="mt-8 space-y-4">
            {FEATURES.map(({ icon: Icon, text }, i) => (
              <li
                key={text}
                className="flex animate-fade-in-up items-start gap-3"
                style={{ animationDelay: `${220 + i * 90}ms` }}
              >
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white/10 text-white">
                  <Icon className="h-4 w-4" />
                </span>
                <span className="pt-1 text-sm text-brand-50">{text}</span>
              </li>
            ))}
          </ul>
        </div>

        <p className="relative text-xs text-brand-200/70">
          &copy; {new Date().getFullYear()} SmartSpend. Built for DUT students.
        </p>
      </div>

      {/* Form panel */}
      <div className="relative flex flex-1 flex-col justify-center px-4 py-12 sm:px-6 lg:px-16">
        <div className="absolute right-5 top-5 lg:right-8 lg:top-8">
          <ThemeToggle light={false} />
        </div>

        <div key={title} className="mx-auto w-full max-w-sm animate-fade-in-up">
          <Logo size={36} className="mb-8 animate-pop-in lg:hidden" />

          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">{title}</h1>
          {subtitle && <p className="mt-1.5 text-sm text-slate-500 dark:text-slate-400">{subtitle}</p>}

          <div className="mt-7">{children}</div>
        </div>
      </div>
    </div>
  );
}
