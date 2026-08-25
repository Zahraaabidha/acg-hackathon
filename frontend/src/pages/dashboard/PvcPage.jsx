import { useOutletContext } from "react-router-dom";
import { MaterialSection } from "../../components/MaterialSection";
import { shiftedForecastSeries } from "../../lib/whatIf";

export default function PvcPage() {
  const { data, crudePct, fxPct } = useOutletContext();
  const material = data.materials.pvc_resin_price;

  return (
    <div className="space-y-6 pb-16">
      <div className="mb-1">
        <p className="eyebrow mb-1">PVC Resin</p>
        <h1 className="font-display text-3xl font-semibold tracking-tight text-[var(--color-ink-primary)]">
          PVC Resin Forecast
        </h1>
        <p className="mt-1.5 max-w-2xl text-[13px] text-[var(--color-ink-muted)]">
          Ridge regression, 6-month horizon, 90% prediction interval - what-if sliders carry over from Overview.
        </p>
      </div>

      <MaterialSection material={material} shifted={shiftedForecastSeries(material, crudePct, fxPct)} />
    </div>
  );
}
