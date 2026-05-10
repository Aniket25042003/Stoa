"use client";

export function HeroDashboardOrbit() {
  return (
    <div className="relative">
      <div className="absolute -inset-8 rounded-[2.4rem] bg-gradient-to-br from-primary/30 via-violet-pulse/20 to-transparent blur-3xl" />
      <div className="absolute inset-x-[20%] -bottom-8 h-20 rounded-full bg-primary/35 blur-2xl" />
      <div className="relative [perspective:1400px]">
        <div className="relative overflow-hidden rounded-[2rem] border border-white/20 bg-slate-deep p-5 text-white shadow-card [transform:rotateY(-14deg)_rotateX(7deg)]">
          <div className="absolute inset-0 opacity-40 [background-image:linear-gradient(to_right,rgb(255_255_255_/_0.08)_1px,transparent_1px),linear-gradient(to_bottom,rgb(255_255_255_/_0.08)_1px,transparent_1px)] [background-size:32px_32px]" />
          <div className="relative flex items-center justify-between gap-3 border-b border-white/15 pb-4">
            <div>
              <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-inverse-primary">Dashboard</p>
              <p className="mt-1 font-display text-lg font-bold">Autonomous GTM cockpit</p>
            </div>
            <span className="rounded-full border border-white/20 bg-white/10 px-3 py-1 font-mono text-[10px] uppercase tracking-[0.14em] text-white/85">
              Live
            </span>
          </div>

          <div className="relative mt-4 grid grid-cols-3 gap-3">
            {[
              ["Signals", "1.2k"],
              ["Runs", "18"],
              ["Health", "94%"],
            ].map(([label, value]) => (
              <div key={label} className="rounded-xl border border-white/12 bg-white/6 p-3">
                <p className="font-mono text-[10px] uppercase tracking-[0.12em] text-white/60">{label}</p>
                <p className="mt-2 font-display text-xl font-bold">{value}</p>
              </div>
            ))}
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <div className="rounded-xl border border-white/12 bg-white/6 p-3">
              <p className="font-mono text-[10px] uppercase tracking-[0.12em] text-white/62">Pipeline trend</p>
              <div className="mt-3 h-16 rounded-lg bg-[linear-gradient(180deg,rgb(139_92_246_/_0.28),transparent_70%)]" />
            </div>
            <div className="rounded-xl border border-white/12 bg-white/6 p-3">
              <p className="font-mono text-[10px] uppercase tracking-[0.12em] text-white/62">Channel share</p>
              <div className="mt-4 flex items-end gap-1.5">
                {[35, 55, 42, 62, 51, 70].map((h, i) => (
                  <span key={i} className="w-4 rounded-t-sm bg-gradient-to-t from-primary to-violet-pulse" style={{ height: `${h}%` }} />
                ))}
              </div>
            </div>
          </div>

          <div className="pointer-events-none absolute inset-x-0 top-0 h-24 animate-scan bg-gradient-to-b from-white/10 to-transparent" />
        </div>
      </div>
    </div>
  );
}
