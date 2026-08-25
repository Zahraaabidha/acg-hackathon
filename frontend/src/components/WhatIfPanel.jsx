import { Card } from "./Card";

function SliderRow({ label, value, onChange, unit }) {
  return (
    <div>
      <div className="flex items-baseline justify-between">
        <label className="text-[13px] font-semibold text-[var(--color-ink-primary)]">{label}</label>
        <span
          className="tabular-nums text-[13px] font-bold"
          style={{ color: value === 0 ? "var(--color-ink-muted)" : "var(--color-brand)" }}
        >
          {value > 0 ? "+" : ""}{value}{unit}
        </span>
      </div>
      <input
        type="range"
        min={-30}
        max={30}
        step={1}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="mt-2 w-full accent-[var(--color-brand)]"
      />
      <div className="mt-1 flex justify-between text-[10px] text-[var(--color-ink-muted)]">
        <span>-30%</span>
        <span>0</span>
        <span>+30%</span>
      </div>
    </div>
  );
}

export function WhatIfPanel({ crudePct, fxPct, onCrudeChange, onFxChange }) {
  const isActive = crudePct !== 0 || fxPct !== 0;

  return (
    <Card
      eyebrow="Live Simulation"
      title="What-if scenario"
      subtitle="Simple linear recomputation from the deployed Ridge model's stored coefficients - client-side only, no live model call. Shifts the same-month input; lag and rolling context stay fixed."
      action={
        isActive && (
          <button
            onClick={() => {
              onCrudeChange(0);
              onFxChange(0);
            }}
            className="rounded-full border border-[var(--color-hairline)] px-3 py-1 text-[11px] font-semibold uppercase tracking-wide text-[var(--color-ink-secondary)] hover:bg-[var(--color-page)]"
          >
            Reset
          </button>
        )
      }
    >
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        <SliderRow label="Crude oil price" value={crudePct} onChange={onCrudeChange} unit="%" />
        <SliderRow label="USD/INR exchange rate" value={fxPct} onChange={onFxChange} unit="%" />
      </div>
    </Card>
  );
}
