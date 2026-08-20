import { PillButton } from "../PillButton";
import { formatFeatureLabel } from "../../lib/format";

function MaterialCard({ material }) {
  const top = [...material.featureImportances]
    .sort((a, b) => Math.abs(b.coefficient) - Math.abs(a.coefficient))
    .slice(0, 2);

  return (
    <div className="rounded-[4px] border border-[var(--color-hairline)] bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center gap-2.5">
        <span className="inline-flex h-2.5 w-2.5 rounded-full" style={{ backgroundColor: material.color }} />
        <p className="font-display text-base font-semibold text-[var(--color-ink-900)]">{material.label}</p>
      </div>

      <div className="mb-5 grid grid-cols-2 gap-4">
        <div>
          <p className="eyebrow mb-1">RMSE (Ridge)</p>
          <p className="tabular-nums font-display text-xl font-semibold text-[var(--color-ink-900)]">
            {material.accuracy.ridge.RMSE.toFixed(0)}
          </p>
          <p className="text-[11px] text-[var(--color-ink-muted)]">
            vs {material.accuracy.naive.RMSE.toFixed(0)} naive
          </p>
        </div>
        <div>
          <p className="eyebrow mb-1">Directional Acc.</p>
          <p className="tabular-nums font-display text-xl font-semibold text-[var(--color-ink-900)]">
            {material.accuracy.ridge.directionalAccuracy.toFixed(0)}%
          </p>
          <p className="text-[11px] text-[var(--color-ink-muted)]">
            vs {material.accuracy.naive.directionalAccuracy.toFixed(0)}% naive
          </p>
        </div>
      </div>

      <p className="eyebrow mb-2">Top drivers</p>
      <ul className="space-y-1.5">
        {top.map((f) => (
          <li key={f.feature} className="flex items-center justify-between text-[13px]">
            <span className="capitalize text-[var(--color-ink-secondary)]">{formatFeatureLabel(f.feature)}</span>
            <span className="tabular-nums font-semibold text-[var(--color-ink-900)]">
              {f.coefficient > 0 ? "+" : ""}
              {f.coefficient.toFixed(1)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function ModelPreview({ data }) {
  if (!data) return null;
  const materials = Object.values(data.materials);

  return (
    <section id="model" className="bg-[var(--color-page)] py-16 sm:py-20 lg:py-24">
      <div className="mx-auto max-w-[1200px] px-5 sm:px-8 lg:px-12">
        <div className="mb-10 flex flex-col items-start justify-between gap-6 sm:flex-row sm:items-end">
          <div>
            <p className="eyebrow mb-4">The model</p>
            <h2
              className="font-display font-medium text-[var(--color-ink-900)]"
              style={{ fontSize: "clamp(1.8rem, 3.6vw, 2.6rem)", lineHeight: 1.1, letterSpacing: "-0.02em" }}
            >
              Ridge regression, evaluated
              <br className="hidden sm:block" /> honestly against a naive baseline.
            </h2>
          </div>
          <PillButton label="View full dashboard" variant="dark" href="/dashboard" />
        </div>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
          {materials.map((m) => (
            <MaterialCard key={m.key} material={m} />
          ))}
        </div>
      </div>
    </section>
  );
}
