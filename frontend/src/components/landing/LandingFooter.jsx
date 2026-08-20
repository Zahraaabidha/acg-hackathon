export function LandingFooter() {
  return (
    <footer className="border-t border-white/10 bg-[#0a0a0a] py-10">
      <div className="mx-auto flex max-w-[1200px] flex-col items-start justify-between gap-4 px-5 sm:flex-row sm:items-center sm:px-8 lg:px-12">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-white">
            <span className="font-display text-[9px] font-bold text-[var(--color-ink-900)]">ACG</span>
          </div>
          <span className="text-[13px] text-white/60">ACG Smart Buy · Raw Material Intelligence</span>
        </div>
        <p className="text-[12px] text-white/40">
          Static demo — no live API calls in the browser. All figures generated from real FRED/market data.
        </p>
      </div>
    </footer>
  );
}
