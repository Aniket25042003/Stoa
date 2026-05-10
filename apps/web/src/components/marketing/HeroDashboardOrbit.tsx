"use client";

const trendPoints = [
  [0, 42],
  [18, 58],
  [36, 48],
  [54, 72],
  [72, 62],
  [90, 88],
  [108, 78],
  [124, 92],
];
const barValues = [38, 52, 45, 68, 55, 72, 48, 61];

export function HeroDashboardOrbit() {
  const linePath = trendPoints.map(([x, y], i) => `${i === 0 ? "M" : "L"} ${x} ${100 - y}`).join(" ");
  const areaPath = `${linePath} L 124 100 L 0 100 Z`;

  return (
    <div className="relative mx-auto w-full max-w-lg lg:max-w-none">
      <div className="absolute -inset-8 rounded-[2.4rem] bg-gradient-to-br from-primary/35 via-violet-pulse/25 to-transparent blur-3xl motion-safe:animate-pulse" />
      <div className="absolute inset-x-[15%] -bottom-10 h-24 rounded-full bg-primary/40 blur-2xl motion-safe:opacity-90 motion-safe:animate-pulse" />
      <div className="relative [perspective:1400px]">
        <div className="relative overflow-hidden rounded-[2rem] border border-white/20 bg-slate-deep p-4 text-white shadow-card sm:p-5 md:[transform:rotateY(-14deg)_rotateX(7deg)]">
          {/* Energetic grid + dual scan */}
          <div className="hero-dashboard-grid absolute inset-0 opacity-50 [background-image:linear-gradient(to_right,rgb(255_255_255_/_0.1)_1px,transparent_1px),linear-gradient(to_bottom,rgb(255_255_255_/_0.1)_1px,transparent_1px)] [background-size:32px_32px]" />
          <div className="pointer-events-none absolute inset-x-0 top-0 h-28 animate-scan bg-gradient-to-b from-indigo-400/25 to-transparent motion-reduce:animate-none" />
          <div
            className="pointer-events-none absolute inset-x-0 bottom-0 h-20 opacity-70 motion-reduce:opacity-40"
            style={{
              background: "linear-gradient(to top, rgb(139 92 246 / 22%), transparent)",
            }}
          />

          <div className="relative flex flex-wrap items-start justify-between gap-3 border-b border-white/15 pb-3 sm:pb-4">
            <div className="min-w-0">
              <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-inverse-primary">Dashboard</p>
              <p className="mt-1 font-display text-base font-bold sm:text-lg">Autonomous GTM cockpit</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="hidden font-mono text-[10px] text-white/45 sm:inline">Last sync · 2m ago</span>
              <span className="rounded-full border border-emerald-400/35 bg-emerald-500/15 px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.12em] text-emerald-200">
                Live
              </span>
            </div>
          </div>

          <div className="relative mt-3 grid grid-cols-3 gap-2 sm:gap-3">
            {[
              ["Pipeline phase", "Writing", "+12%"],
              ["Signals indexed", "1.24k", "+8%"],
              ["Quality score", "94", "steady"],
            ].map(([label, value, delta]) => (
              <div key={label} className="rounded-xl border border-white/12 bg-white/8 p-2.5 sm:p-3">
                <p className="font-mono text-[9px] uppercase tracking-[0.1em] text-white/55 sm:text-[10px]">{label}</p>
                <p className="mt-1.5 font-display text-lg font-bold tabular-nums sm:text-xl">{value}</p>
                <p className="mt-1 font-mono text-[10px] text-emerald-300/90">{delta}</p>
              </div>
            ))}
          </div>

          <div className="relative mt-3 grid gap-3 sm:grid-cols-2">
            <div className="rounded-xl border border-white/12 bg-white/6 p-3">
              <div className="flex items-center justify-between gap-2">
                <p className="font-mono text-[10px] uppercase tracking-[0.12em] text-white/65">Pipeline trend</p>
                <span className="rounded bg-white/10 px-1.5 py-0.5 font-mono text-[9px] text-white/70">7d</span>
              </div>
              <svg viewBox="0 0 124 100" className="mt-2 h-20 w-full overflow-visible sm:h-24" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="heroTrendFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="rgb(139 92 246)" stopOpacity="0.45" />
                    <stop offset="100%" stopColor="rgb(99 102 241)" stopOpacity="0.05" />
                  </linearGradient>
                  <linearGradient id="heroTrendStroke" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="rgb(129 140 248)" />
                    <stop offset="100%" stopColor="rgb(167 139 250)" />
                  </linearGradient>
                </defs>
                <path d={areaPath} fill="url(#heroTrendFill)" />
                <path
                  d={linePath}
                  fill="none"
                  stroke="url(#heroTrendStroke)"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                {trendPoints.map(([x, y], i) => (
                  <circle key={i} cx={x} cy={100 - y} r="3" fill="white" className="opacity-90" />
                ))}
              </svg>
              <div className="mt-2 flex justify-between font-mono text-[9px] text-white/45">
                <span>Mon</span>
                <span>Thu</span>
                <span>Today</span>
              </div>
            </div>

            <div className="rounded-xl border border-white/12 bg-white/6 p-3">
              <div className="flex items-center justify-between gap-2">
                <p className="font-mono text-[10px] uppercase tracking-[0.12em] text-white/65">Channel share</p>
                <span className="text-[9px] text-white/45">by intent</span>
              </div>
              <div className="mt-3 flex h-24 items-end justify-between gap-1 border-b border-white/10 pb-1">
                {barValues.map((h, i) => (
                  <div key={i} className="flex flex-1 flex-col items-center gap-1">
                    <div
                      className="origin-bottom w-full max-w-[28px] rounded-t-sm bg-gradient-to-t from-primary via-indigo-400 to-violet-300 shadow-[0_0_12px_rgb(139_92_246_/_0.35)] motion-safe:animate-[bar-rise_0.55s_ease-out_both] motion-reduce:animate-none"
                      style={{
                        height: `${h}%`,
                        animationDelay: `${i * 0.05}s`,
                      }}
                    />
                    <span className="font-mono text-[8px] uppercase text-white/35">{["SR", "LI", "EM", "CM", "RD", "PR", "EV", "OT"][i]}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="relative mt-3 flex flex-wrap items-center gap-2 rounded-lg border border-white/10 bg-black/25 px-2.5 py-2 font-mono text-[10px] text-white/65">
            <span className="inline-flex items-center gap-1.5 rounded-md bg-white/8 px-2 py-0.5 text-white/85">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
              Run #284 · ingest stable
            </span>
            <span className="text-white/40">·</span>
            <span>Next milestone: narrative QA</span>
          </div>
        </div>
      </div>
    </div>
  );
}
