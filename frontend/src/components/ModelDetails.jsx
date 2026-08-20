import { useState } from "react";
import { formatFeatureLabel } from "../lib/format";

export function ModelDetails({ accuracy, featureImportances }) {
  const [open, setOpen] = useState(false);
  const topFeatures = [...featureImportances]
    .sort((a, b) => Math.abs(b.coefficient) - Math.abs(a.coefficient))
    .slice(0, 3);

  return (
    <div className="mt-5 border-t border-[var(--color-hairline)] pt-4">
      <button
        onClick={() => setOpen((v) => !v)}
        className="eyebrow hover:text-[var(--color-ink-secondary)]"
      >
        {open ? "Hide" : "Show"} model details
        <span className="ml-1">{open ? "−" : "+"}</span>
      </button>

      {open && (
        <div className="mt-3 grid grid-cols-1 gap-4 text-[12px] sm:grid-cols-2">
          <div>
            <p className="font-semibold text-[var(--color-ink-secondary)]">Test-set accuracy (Ridge vs naive)</p>
            <dl className="mt-1.5 space-y-1 tabular-nums text-[var(--color-ink-muted)]">
              <div className="flex justify-between">
                <dt>RMSE</dt>
                <dd>{accuracy.ridge.RMSE.toFixed(1)} vs {accuracy.naive.RMSE.toFixed(1)}</dd>
              </div>
              <div className="flex justify-between">
                <dt>MAPE</dt>
                <dd>{accuracy.ridge.MAPE.toFixed(1)}% vs {accuracy.naive.MAPE.toFixed(1)}%</dd>
              </div>
              <div className="flex justify-between">
                <dt>Directional accuracy</dt>
                <dd>{accuracy.ridge.directionalAccuracy.toFixed(0)}% vs {accuracy.naive.directionalAccuracy.toFixed(0)}%</dd>
              </div>
            </dl>
          </div>
          <div>
            <p className="font-semibold text-[var(--color-ink-secondary)]">Top drivers (standardized coefficient)</p>
            <ul className="mt-1.5 space-y-1 text-[var(--color-ink-muted)]">
              {topFeatures.map((f) => (
                <li key={f.feature} className="flex justify-between">
                  <span className="capitalize">{formatFeatureLabel(f.feature)}</span>
                  <span className="tabular-nums">{f.coefficient > 0 ? "+" : ""}{f.coefficient.toFixed(1)}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
