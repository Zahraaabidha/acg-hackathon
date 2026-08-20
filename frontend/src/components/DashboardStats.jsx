const RECOMMENDATION_ACCENT = {
  "Buy now": "text-[var(--color-good)]",
  Wait: "text-[#b57900]",
  "Neutral / Monitor": "text-[var(--color-ink-primary)]",
};

function StatTile({ label, value, sub, accent }) {
  return (
    <div className="rounded-[4px] border border-[var(--color-hairline)] bg-white p-5 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md">
      <p className="eyebrow mb-2">{label}</p>
      <p className={`font-display text-3xl font-semibold tracking-tight ${accent ?? "text-[var(--color-ink-primary)]"}`}>
        {value}
      </p>
      <p className="mt-1 text-[12px] text-[var(--color-ink-muted)]">{sub}</p>
    </div>
  );
}

export function DashboardStats({ data }) {
  const aluminium = data.materials.aluminium_price;
  const pvc = data.materials.pvc_resin_price;
  const alSignal = aluminium.forecast[0];
  const pvcSignal = pvc.forecast[0];
  const rmShare = Math.round(data.costExposureAssumptions.rmCostShareTotal * 100);

  return (
    <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
      <StatTile
        label="Aluminium Signal"
        value={alSignal.recommendation}
        sub={`${alSignal.confidence} confidence · ${alSignal.month}`}
        accent={RECOMMENDATION_ACCENT[alSignal.recommendation]}
      />
      <StatTile
        label="PVC Resin Signal"
        value={pvcSignal.recommendation}
        sub={`${pvcSignal.confidence} confidence · ${pvcSignal.month}`}
        accent={RECOMMENDATION_ACCENT[pvcSignal.recommendation]}
      />
      <StatTile
        label="RM Cost Coverage"
        value={`${rmShare}%`}
        sub="Aluminium + PVC of total cost base"
      />
      <StatTile
        label="Shock Alerts"
        value={data.riskAlerts.length}
        sub="Driver-months flagged, full history"
        accent="text-[var(--color-critical)]"
      />
    </div>
  );
}
