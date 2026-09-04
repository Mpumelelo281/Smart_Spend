// Flat-illustration phone mockup for the login branding panel — built
// from CSS/SVG rather than a photo composite, since that's what the
// reference design actually is (a vector illustration, not a screenshot
// pasted onto a stock photo). Numbers are illustrative, not live data —
// but the total matches the app's real fixed NSFAS allowance (R1650, see
// StudentProfile.allowance_amount) so it isn't a made-up figure either.

const CATEGORIES = [
  { label: "Clothes", amount: "R 300", color: "#a78bfa" },
  { label: "Food", amount: "R 650", color: "#fbbf24" },
  { label: "Transport", amount: "R 350", color: "#fb923c" },
  { label: "Entertainment", amount: "R 150", color: "#f472b6" },
  { label: "Other", amount: "R 200", color: "#60a5fa" },
];

// Donut ring segments, matching the amounts above (sum to 100%).
const SEGMENTS = [
  { color: "#a78bfa", pct: 18 },
  { color: "#fbbf24", pct: 39 },
  { color: "#fb923c", pct: 21 },
  { color: "#f472b6", pct: 9 },
  { color: "#60a5fa", pct: 13 },
];

function DonutChart() {
  const radius = 34;
  const circumference = 2 * Math.PI * radius;
  let offset = 0;

  return (
    <svg viewBox="0 0 88 88" className="h-24 w-24">
      <circle cx="44" cy="44" r={radius} fill="none" stroke="#f1f5f9" strokeWidth="10" />
      {SEGMENTS.map((seg, i) => {
        const dash = (seg.pct / 100) * circumference;
        const circle = (
          <circle
            key={i}
            cx="44"
            cy="44"
            r={radius}
            fill="none"
            stroke={seg.color}
            strokeWidth="10"
            strokeDasharray={`${dash} ${circumference - dash}`}
            strokeDashoffset={-offset}
            strokeLinecap="round"
            transform="rotate(-90 44 44)"
          />
        );
        offset += dash;
        return circle;
      })}
    </svg>
  );
}

export default function PhoneMockup() {
  return (
    // Scale is applied on this outer wrapper (not the animated element
    // itself) since the `float` keyframe sets `transform: translateY(...)`
    // directly — putting a `scale-*` utility on the same element would have
    // Tailwind's composited `transform` clobbered by the animation's own
    // transform value every frame, silently dropping the scale.
    <div className="flex justify-center lg:scale-110 xl:scale-125 2xl:scale-150">
      <div className="relative w-[220px] animate-float pb-6 pl-4 pr-10 pt-4">
        {/* Phone frame */}
        <div className="relative rounded-[2.2rem] bg-slate-900 p-2 shadow-2xl ring-1 ring-white/10">
          <div className="rounded-[1.7rem] bg-white p-4">
            <div className="mb-3 flex items-center justify-between">
              <span className="text-[11px] font-semibold text-slate-500">Monthly Overview</span>
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            </div>

            <div className="relative mx-auto flex h-24 w-24 items-center justify-center">
              <DonutChart />
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-sm font-extrabold text-slate-900">R 1 650</span>
                <span className="text-[9px] text-slate-400">Monthly Allowance</span>
              </div>
            </div>

            <div className="mt-4 space-y-2">
              {CATEGORIES.map((c) => (
                <div key={c.label} className="flex items-center justify-between text-[10px]">
                  <span className="flex items-center gap-1.5 text-slate-500">
                    <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: c.color }} />
                    {c.label}
                  </span>
                  <span className="font-semibold text-slate-700">{c.amount}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Floating badges */}
        <div className="absolute -right-2 top-6 flex h-14 w-14 rotate-6 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-400 to-emerald-600 shadow-xl">
          <svg viewBox="0 0 24 24" className="h-7 w-7" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 3l7 3v5c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6l7-3Z" />
            <path d="M9 12l2 2 4-4" />
          </svg>
        </div>

        <div className="absolute -right-4 top-32 flex h-12 w-12 -rotate-6 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-400 to-brand-600 shadow-xl">
          <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 17l5-5 3 3 6-7" />
            <path d="M14 8h4v4" />
          </svg>
        </div>

        {/* Coin stack */}
        <div className="absolute bottom-0 right-2 flex flex-col items-center">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="h-3 w-11 rounded-full bg-gradient-to-b from-amber-300 to-amber-500 shadow-md"
              style={{ marginTop: i === 0 ? 0 : -6 }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
