function StatTile({ label, value, sub }) {
  return (
    <div className="rounded-[4px] border border-[var(--color-hairline)] bg-white p-5 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md">
      <p className="eyebrow mb-2">{label}</p>
      <p className="font-display text-4xl font-semibold tracking-tight text-[var(--color-ink-primary)]">{value}</p>
      <p className="mt-1 text-[12px] text-[var(--color-ink-muted)]">{sub}</p>
    </div>
  );
}

function buildStats(data) {
  const aluminium = data.materials.aluminium_price;
  const pvc = data.materials.pvc_resin_price;
  const horizon = aluminium.forecast.length;
  const rmShare = Math.round(data.costExposureAssumptions.rmCostShareTotal * 100);
  const alDir = Math.round(aluminium.accuracy.ridge.directionalAccuracy);
  const pvcDir = Math.round(pvc.accuracy.ridge.directionalAccuracy);
  const dirValue = alDir === pvcDir ? `${alDir}%` : `${Math.min(alDir, pvcDir)}–${Math.max(alDir, pvcDir)}%`;

  return [
    { label: "RM Cost Coverage", value: `${rmShare}%`, sub: "of ACG's raw material cost base modeled" },
    { label: "Forecast Horizon", value: `${horizon}mo`, sub: "Ridge regression, both materials" },
    { label: "Directional Accuracy", value: dirValue, sub: "vs. naive baseline (test set)" },
    { label: "Shock Alerts Flagged", value: data.riskAlerts.length, sub: "driver-months, incl. 2020 COVID collapse" },
  ];
}

export function StatsStrip({ data }) {
  if (!data) {
    return (
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-[120px] animate-pulse rounded-[4px] border border-[var(--color-hairline)] bg-white" />
        ))}
      </div>
    );
  }

  const stats = buildStats(data);

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {stats.map((s) => (
        <StatTile key={s.label} {...s} />
      ))}
    </div>
  );
}
