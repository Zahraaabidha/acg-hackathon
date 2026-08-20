export function NarrativeCallout({ narrative, color }) {
  if (!narrative) return null;

  return (
    <div
      className="rounded-[4px] border-l-[3px] bg-[var(--color-page)] px-4 py-3.5 text-[13px] leading-relaxed text-[var(--color-ink-primary)]"
      style={{ borderColor: color }}
    >
      {narrative}
    </div>
  );
}
