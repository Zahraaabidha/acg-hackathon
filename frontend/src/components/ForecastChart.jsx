import { Area, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatPrice, monthLabel } from "../lib/format";

function buildChartData(history, forecast, shifted) {
  const historyPoints = history.map((h) => ({ month: h.month, actualPrice: h.price }));
  const forecastPoints = forecast.map((f, i) => ({
    month: f.month,
    forecastedPrice: f.forecastedPrice,
    range: [f.intervalLow, f.intervalHigh],
    shiftedPrice: shifted ? shifted[i] : undefined,
  }));
  return [...historyPoints, ...forecastPoints];
}

function ChartTooltip({ active, payload, label, color }) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload;

  return (
    <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-2 text-xs shadow-md">
      <p className="font-semibold text-[var(--color-ink-primary)]">{monthLabel(label)}</p>
      {point.actualPrice !== undefined && (
        <p className="mt-1 text-[var(--color-ink-secondary)]">
          Actual: <span className="tabular-nums font-medium text-[var(--color-ink-primary)]">{formatPrice(point.actualPrice)}</span>
        </p>
      )}
      {point.forecastedPrice !== undefined && (
        <p className="text-[var(--color-ink-secondary)]">
          Forecast: <span className="tabular-nums font-medium" style={{ color }}>{formatPrice(point.forecastedPrice)}</span>
        </p>
      )}
      {point.shiftedPrice !== undefined && (
        <p className="text-[var(--color-ink-secondary)]">
          What-if: <span className="tabular-nums font-medium" style={{ color }}>{formatPrice(point.shiftedPrice)}</span>
        </p>
      )}
      {point.range && (
        <p className="mt-1 text-[var(--color-ink-muted)]">
          90% interval: {formatPrice(point.range[0])}–{formatPrice(point.range[1])}
        </p>
      )}
    </div>
  );
}

export function ForecastChart({ history, forecast, color, shifted }) {
  const data = buildChartData(history, forecast, shifted);

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
          <CartesianGrid stroke="var(--color-hairline)" vertical={false} />
          <XAxis
            dataKey="month"
            tickFormatter={monthLabel}
            tick={{ fontSize: 11, fill: "var(--color-ink-muted)" }}
            axisLine={{ stroke: "var(--color-hairline)" }}
            tickLine={false}
            minTickGap={24}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "var(--color-ink-muted)" }}
            axisLine={false}
            tickLine={false}
            width={52}
            tickFormatter={(v) => formatPrice(v)}
          />
          <Tooltip content={<ChartTooltip color={color} />} />
          <Area
            dataKey="range"
            stroke="none"
            fill={color}
            fillOpacity={0.14}
            isAnimationActive={false}
            connectNulls
          />
          <Line
            dataKey="actualPrice"
            stroke="var(--color-ink-primary)"
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
            connectNulls={false}
          />
          <Line
            dataKey="forecastedPrice"
            stroke={color}
            strokeWidth={2}
            dot={{ r: 3, fill: color, strokeWidth: 0 }}
            isAnimationActive={false}
            connectNulls
          />
          {shifted && (
            <Line
              dataKey="shiftedPrice"
              stroke={color}
              strokeWidth={2}
              strokeDasharray="5 4"
              dot={{ r: 3, fill: "var(--color-surface)", stroke: color, strokeWidth: 2 }}
              isAnimationActive={false}
              connectNulls
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
