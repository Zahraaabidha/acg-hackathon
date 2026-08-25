import { PillButton } from "../PillButton";

export function Hero() {
  return (
    <section
      id="overview"
      className="relative flex min-h-screen flex-col overflow-hidden"
      style={{ backgroundColor: "#0a0a0a" }}
    >
      <video
        className="pointer-events-none absolute inset-0 h-full w-full object-cover"
        src="/hero-bg.mp4"
        autoPlay
        loop
        muted
        playsInline
        aria-hidden="true"
      />
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

        <div className="mx-auto w-full max-w-[1200px] px-5 pb-40 sm:px-8 sm:pb-44 lg:px-12 lg:pb-48">
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

          <div className="mt-8 flex flex-col items-start gap-4 sm:mt-12 sm:flex-row sm:items-center sm:gap-5">
            <PillButton label="Open Dashboard" variant="brand" href="/dashboard" />
            <a
              href="#how-it-works"
              className="text-[13px] font-medium text-white transition-colors hover:text-white"
            >
              See how it works ↓
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
