export function FullScreenMessage({ title, detail, hint }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--color-page)] px-6">
      <div className="max-w-md text-center">
        <h2 className="text-lg font-semibold text-[var(--color-ink-primary)]">{title}</h2>
        {detail && <p className="mt-2 text-sm text-[var(--color-ink-secondary)]">{detail}</p>}
        {hint && (
          <code className="mt-4 inline-block rounded-lg bg-[var(--color-surface)] px-3 py-2 text-xs text-[var(--color-ink-secondary)]">
            {hint}
          </code>
        )}
      </div>
    </div>
  );
}
