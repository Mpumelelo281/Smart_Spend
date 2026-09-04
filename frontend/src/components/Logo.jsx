// A tilted card + coin composition, in a gradient badge — reads
// instantly as "payments/spending" the way Stripe/Revolut-style app
// icons do. Pure SVG so it stays crisp at any size and needs no image
// asset; a soft drop-shadow on the card gives it real depth instead of
// sitting flat on the badge.
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
        <linearGradient id="ss-badge" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#34d399" />
          <stop offset="100%" stopColor="#15803d" />
        </linearGradient>
        <linearGradient id="ss-card" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#ffffff" />
          <stop offset="100%" stopColor="#dcfce7" />
        </linearGradient>
        <linearGradient id="ss-coin" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#ffd36e" />
          <stop offset="100%" stopColor="#f5a524" />
        </linearGradient>
        <filter id="ss-shadow" x="-50%" y="-50%" width="200%" height="200%">
          <feDropShadow dx="0" dy="1.2" stdDeviation="1.4" floodColor="#052e1f" floodOpacity="0.35" />
        </filter>
      </defs>

      <rect width="40" height="40" rx="11" fill="url(#ss-badge)" />

      {/* Card, tilted for depth */}
      <g transform="rotate(-10 17 19)" filter="url(#ss-shadow)">
        <rect x="6" y="12" width="22" height="14.5" rx="3" fill="url(#ss-card)" />
        <rect x="9" y="16" width="5.5" height="4" rx="1.1" fill="#f5a524" />
        <rect x="9" y="22.3" width="10" height="1.6" rx="0.8" fill="#86efac" />
        <rect x="9" y="24.6" width="6" height="1.6" rx="0.8" fill="#bbf7d0" />
      </g>

      {/* Coin, overlapping bottom-right — "R" for Rand */}
      <circle cx="29.5" cy="27.5" r="6.6" fill="url(#ss-coin)" filter="url(#ss-shadow)" />
      <circle cx="29.5" cy="27.5" r="4.7" fill="none" stroke="#fff" strokeOpacity="0.5" strokeWidth="0.8" />
      <text
        x="29.5"
        y="30.6"
        textAnchor="middle"
        fontSize="7"
        fontWeight="800"
        fontFamily="ui-sans-serif, system-ui, sans-serif"
        fill="#fff"
      >
        R
      </text>
    </svg>
  );
}

export default function Logo({ size = 36, wordmark = true, variant = "auto", tagline, className = "" }) {
  const wordmarkColor =
    variant === "light"
      ? "text-white"
      : variant === "dark"
        ? "text-slate-900"
        : "text-slate-900 dark:text-white";
  const taglineColor = variant === "light" ? "text-white/60" : "text-slate-400 dark:text-slate-500";

  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      <Mark size={size} />
      {wordmark && (
        <div>
          <span className={`block text-xl font-extrabold leading-none tracking-tight ${wordmarkColor}`}>
            SmartSpend
          </span>
          {tagline && <span className={`text-xs ${taglineColor}`}>{tagline}</span>}
        </div>
      )}
    </div>
  );
}
