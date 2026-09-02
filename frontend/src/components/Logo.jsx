// Wallet + upward trend, in a gradient badge — "budgeting" and "smart"
// as one small mark. Pure SVG so it stays crisp at any size and needs no
// image asset.
function Mark({ size }) {
  return (
    <svg
      viewBox="0 0 40 40"
      width={size}
      height={size}
      className="shrink-0"
      role="img"
      aria-label="SmartSpend logo"
    >
      <defs>
        <linearGradient id="smartspend-mark" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#38a3f8" />
          <stop offset="100%" stopColor="#1d4ed8" />
        </linearGradient>
      </defs>
      <rect width="40" height="40" rx="11" fill="url(#smartspend-mark)" />
      <path
        d="M9 15.5c0-1.4 1.1-2.5 2.5-2.5h15c1.1 0 2 .9 2 2v1"
        fill="none"
        stroke="#fff"
        strokeWidth="2"
        strokeLinecap="round"
      />
      <rect x="9" y="15.5" width="22" height="14" rx="3" fill="none" stroke="#fff" strokeWidth="2" />
      <circle cx="25.5" cy="22.5" r="1.6" fill="#fff" />
      <path
        d="M13 20.5l3.2 3.2 2.6-2.6 3.7 3.7"
        fill="none"
        stroke="#a8d4ff"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default function Logo({ size = 36, wordmark = true, variant = "auto", className = "" }) {
  const wordmarkColor =
    variant === "light"
      ? "text-white"
      : variant === "dark"
        ? "text-slate-900"
        : "text-slate-900 dark:text-white";

  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      <Mark size={size} />
      {wordmark && (
        <span className={`text-xl font-extrabold tracking-tight ${wordmarkColor}`}>SmartSpend</span>
      )}
    </div>
  );
}
