import { formatPrice, monthLabel } from "../lib/format";

const RECOMMENDATION_STYLE = {
  "Buy now": "bg-[#e6f6e6] text-[#0b6b0b]",
  Wait: "bg-[#fef1d6] text-[#8a5c00]",
  "Neutral / Monitor": "bg-[#f1f0ed] text-[var(--color-ink-secondary)]",
};

function RecommendationBadge({ value }) {
  const style = RECOMMENDATION_STYLE[value] ?? RECOMMENDATION_STYLE["Neutral / Monitor"];
  return (
    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wide ${style}`}>
      {value}
    </span>
  );
}

function ConfidenceBadge({ value }) {
  const isHigh = value === "High";
  return (
    <span className="inline-flex items-center gap-1.5 text-[12px] text-[var(--color-ink-secondary)]">
      <span
        className="inline-block h-1.5 w-1.5 rounded-full"
        style={{ backgroundColor: isHigh ? "var(--color-good)" : "var(--color-warning)" }}
      />
      {value}
    </span>
  );
}

export function SignalTable({ forecast }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-[13px]">
        <thead>
          <tr className="border-b border-[var(--color-hairline)]">
            <th className="eyebrow py-2 pr-3 font-bold">Month</th>
            <th className="eyebrow py-2 pr-3 font-bold">Forecast</th>
            <th className="eyebrow py-2 pr-3 font-bold">Confidence</th>
            <th className="eyebrow py-2 font-bold">Recommendation</th>
          </tr>
        </thead>
        <tbody>
          {forecast.map((row) => (
            <tr key={row.month} className="border-b border-[var(--color-hairline)] last:border-0">
              <td className="py-2.5 pr-3 text-[var(--color-ink-secondary)]">{monthLabel(row.month)}</td>
              <td className="py-2.5 pr-3 tabular-nums font-semibold text-[var(--color-ink-primary)]">
                {formatPrice(row.forecastedPrice)}
              </td>
              <td className="py-2.5 pr-3">
                <ConfidenceBadge value={row.confidence} />
              </td>
              <td className="py-2.5">
                <RecommendationBadge value={row.recommendation} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
