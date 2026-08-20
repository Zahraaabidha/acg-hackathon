import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

const PIPELINE_STEPS = [
  {
    step: "01",
    label: "FETCH",
    heading: "Live FRED and market data pulled monthly.",
    detail: "Crude oil, USD/INR, US electric power PPI, and Baltic Dry Index freight — all free, public series.",
  },
  {
    step: "02",
    label: "CORRELATE",
    heading: "Every driver tested against both targets.",
    detail: "Pearson correlation at 0, 1, 2, 3 and 6-month lags — only drivers clearing 0.5+ get considered.",
  },
  {
    step: "03",
    label: "ENGINEER",
    heading: "Lags, rolling averages, and shock features.",
    detail: "Trimmed to the strongest (predictor, lag) pairs, plus a reusable anomaly z-score as a model input.",
  },
  {
    step: "04",
    label: "FORECAST",
    heading: "Ridge regression beats naive on both materials.",
    detail: "Walk-forward validated, with a 90% prediction interval from test-set residual standard deviation.",
  },
  {
    step: "05",
    label: "SIGNAL",
    heading: "Buy / wait / monitor, weighted by confidence.",
    detail: "Forecast vs. trailing average, tempered by interval width — a wide interval leans toward monitoring.",
  },
  {
    step: "06",
    label: "ALERT",
    heading: "Shock detection validated against real history.",
    detail: "Any driver move beyond 1.5 std devs is flagged — correctly fires on the 2020 COVID collapse.",
  },
];

export function HowItWorks() {
  const [active, setActive] = useState(0);
  const current = PIPELINE_STEPS[active];

  const prev = () => setActive((i) => (i === 0 ? PIPELINE_STEPS.length - 1 : i - 1));
  const next = () => setActive((i) => (i === PIPELINE_STEPS.length - 1 ? 0 : i + 1));

  return (
    <section id="how-it-works" className="overflow-hidden bg-white pb-16 pt-16 sm:pb-24 sm:pt-20 lg:pt-28">
      <div className="mx-auto max-w-[1200px] px-5 sm:px-8 lg:px-12">
        <div className="mb-14 flex flex-col gap-10 lg:mb-16 lg:flex-row lg:items-start lg:justify-between lg:gap-16">
          <div className="flex-shrink-0">
            <p className="eyebrow mb-4">How it works</p>
            <h2
              className="font-display font-medium text-[var(--color-ink-900)]"
              style={{ fontSize: "clamp(1.9rem, 4vw, 3rem)", lineHeight: 1.08, letterSpacing: "-0.03em" }}
            >
              Six-stage pipeline,
              <br />
              from raw FRED data
              <br />
              to a procurement signal.
            </h2>

            <div className="mt-8 flex items-center gap-3">
              <button
                onClick={prev}
                className="flex h-10 w-10 items-center justify-center rounded-full border border-neutral-300 text-neutral-500 transition-colors hover:border-[var(--color-ink-900)] hover:text-[var(--color-ink-900)]"
                aria-label="Previous step"
              >
                <ChevronLeft size={16} />
              </button>
              <button
                onClick={next}
                className="flex h-10 w-10 items-center justify-center rounded-full border border-[var(--color-ink-900)] text-[var(--color-ink-900)] transition-colors hover:bg-[var(--color-ink-900)] hover:text-white"
                aria-label="Next step"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>

          <div className="lg:max-w-lg lg:text-right">
            <p
              key={active}
              className="font-display font-semibold text-[var(--color-ink-900)]"
              style={{ fontSize: "clamp(1.3rem, 2.6vw, 2.1rem)", lineHeight: 1.25, letterSpacing: "-0.02em" }}
            >
              {current.heading}
            </p>
            <p className="mt-4 text-[14px] leading-relaxed text-[var(--color-ink-muted)]">{current.detail}</p>
          </div>
        </div>

        <div>
          <div className="relative mb-5 flex items-center justify-between">
            <div className="absolute left-0 right-0 h-px bg-neutral-200" style={{ top: "50%", transform: "translateY(-50%)" }} />
            {PIPELINE_STEPS.map((s, i) => (
              <button
                key={s.step}
                onClick={() => setActive(i)}
                className="relative z-10 flex-shrink-0 transition-all duration-300"
                aria-label={s.label}
              >
                <span
                  className="block rounded-full transition-all duration-300"
                  style={{
                    width: i === active ? "26px" : "12px",
                    height: i === active ? "26px" : "12px",
                    backgroundColor: i === active ? "var(--color-brand)" : "#d4d4d4",
                  }}
                />
              </button>
            ))}
          </div>

          <div className="flex items-start justify-between">
            {PIPELINE_STEPS.map((s, i) => (
              <button
                key={s.step}
                onClick={() => setActive(i)}
                className="flex-shrink-0 text-center text-[10px] font-bold tracking-[0.14em] transition-colors duration-200"
                style={{
                  width: `${100 / PIPELINE_STEPS.length}%`,
                  color: i === active ? "var(--color-ink-900)" : "#a3a3a3",
                }}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
