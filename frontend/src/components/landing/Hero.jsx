import { PillButton } from "../PillButton";

export function Hero() {
  return (
    <section
      id="overview"
      className="relative flex min-h-screen flex-col overflow-hidden"
      style={{ backgroundColor: "#0a0a0a" }}
    >
      {/* Ambient glow - aluminium blue + PVC orange, echoing the two materials this project forecasts */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(60% 50% at 18% 20%, rgba(42,120,214,0.22), transparent 65%), radial-gradient(55% 45% at 85% 15%, rgba(235,104,52,0.18), transparent 65%)",
        }}
      />
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.05]"
        style={{
          backgroundImage:
            "linear-gradient(to right, #fff 1px, transparent 1px), linear-gradient(to bottom, #fff 1px, transparent 1px)",
          backgroundSize: "56px 56px",
        }}
      />

      <div className="relative z-10 flex flex-1 flex-col">
        <div className="flex-1" />

        <div className="mx-auto w-full max-w-[1200px] px-5 pb-16 sm:px-8 sm:pb-20 lg:px-12 lg:pb-24">
          <p className="mb-5 text-[13px] tracking-wide text-white/60 sm:mb-8">
            ACG Smart Buy · Raw Material Intelligence
          </p>

          <h1
            className="mb-0 font-display font-medium text-white"
            style={{ fontSize: "clamp(2.25rem, 5.5vw, 4.4rem)", lineHeight: 1.08, letterSpacing: "-0.03em" }}
          >
            <span className="block">Forecasting aluminium &amp;</span>
            <span className="block">PVC resin prices before</span>
            <span className="block">they hit procurement.</span>
          </h1>

          <p className="mt-6 max-w-xl text-[15px] leading-relaxed text-white/60 sm:mt-8">
            A causal driver graph, a Ridge regression model beating naive forecasts on both materials, and a
            confidence-weighted buy/wait signal — covering ~70% of ACG's raw material cost base.
          </p>

          <div className="mt-8 flex flex-col items-start gap-4 sm:mt-12 sm:flex-row sm:items-center sm:gap-5">
            <PillButton label="Open Dashboard" variant="brand" href="/dashboard" />
            <a
              href="#how-it-works"
              className="text-[13px] font-medium text-white/70 transition-colors hover:text-white"
            >
              See how it works ↓
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
