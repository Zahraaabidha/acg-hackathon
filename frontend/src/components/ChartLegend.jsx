function Swatch({ color, dashed, children }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-[var(--color-ink-secondary)]">
      <span
        className="inline-block h-0.5 w-4 rounded-full"
        style={{ backgroundColor: dashed ? "transparent" : color, borderTop: dashed ? `2px dashed ${color}` : undefined }}
      />
      {children}
    </span>
  );
}

export function ChartLegend({ color, showWhatIf }) {
  return (
    <div className="mt-3 flex flex-wrap items-center gap-4">
      <Swatch color="var(--color-ink-primary)">Actual</Swatch>
      <Swatch color={color}>Ridge forecast</Swatch>
      <span className="inline-flex items-center gap-1.5 text-xs text-[var(--color-ink-secondary)]">
        <span className="inline-block h-2.5 w-4 rounded-sm" style={{ backgroundColor: color, opacity: 0.25 }} />
        90% interval
      </span>
      {showWhatIf && <Swatch color={color} dashed>What-if</Swatch>}
    </div>
  );
}
