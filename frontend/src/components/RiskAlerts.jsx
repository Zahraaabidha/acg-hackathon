import { Card } from "./Card";
import { formatLabel, formatSigned, monthLabel } from "../lib/format";

function AlertRow({ alert }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-[4px] border border-[var(--color-hairline)] bg-[var(--color-page)] px-3.5 py-2.5">
      <div>
        <p className="text-[13px] font-semibold capitalize text-[var(--color-ink-primary)]">{formatLabel(alert.driver)}</p>
        <p className="text-[11px] capitalize text-[var(--color-ink-muted)]">
          {alert.affectedTargets.map((t) => formatLabel(t)).join(", ")}
        </p>
      </div>
      <div className="text-right">
        <p className="tabular-nums text-[13px] font-bold" style={{ color: "var(--color-critical)" }}>
          {formatSigned(alert.pctChange)}%
        </p>
        <p className="tabular-nums text-[11px] text-[var(--color-ink-muted)]">z = {formatSigned(alert.zScore, 2)}</p>
      </div>
    </div>
  );
}

export function RiskAlerts({ riskAlerts, covidExample, id }) {
  return (
    <Card
      id={id}
      eyebrow="Shock Detection"
      title="Risk / shock alerts"
      subtitle={`${riskAlerts.length} driver-months flagged across history (>1.5 std devs from that driver's own average move) — validated against real events, including the 2020 COVID collapse below.`}
    >
      <div className="mb-4 flex items-center gap-2">
        <span className="inline-flex h-2 w-2 rounded-full" style={{ backgroundColor: "var(--color-critical)" }} />
        <p className="text-[13px] font-semibold text-[var(--color-ink-primary)]">
          Validation example — COVID crude oil collapse, {monthLabel(covidExample[0]?.month ?? "2020-03")} to{" "}
          {monthLabel(covidExample[covidExample.length - 1]?.month ?? "2020-06")}
        </p>
      </div>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {covidExample.map((alert, i) => (
          <AlertRow key={`${alert.month}-${alert.driver}-${i}`} alert={alert} />
        ))}
      </div>
    </Card>
  );
}
