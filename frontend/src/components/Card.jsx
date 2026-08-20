export function Card({ id, eyebrow, title, subtitle, action, children, className = "" }) {
  return (
    <section
      id={id}
      className={`scroll-mt-20 rounded-[4px] border border-[var(--color-hairline)] bg-[var(--color-surface)] p-6 shadow-sm ${className}`}
    >
      {(eyebrow || title || action) && (
        <div className="mb-5 flex items-start justify-between gap-4">
          <div>
            {eyebrow && <p className="eyebrow mb-1.5">{eyebrow}</p>}
            {title && (
              <h3 className="font-display text-lg font-semibold tracking-tight text-[var(--color-ink-primary)]">
                {title}
              </h3>
            )}
            {subtitle && <p className="mt-1.5 text-[13px] leading-relaxed text-[var(--color-ink-secondary)]">{subtitle}</p>}
          </div>
          {action}
        </div>
      )}
      {children}
    </section>
  );
}
