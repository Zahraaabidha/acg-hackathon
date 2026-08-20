import { ArrowRight } from "lucide-react";

// Reusable sliding-text pill CTA - same interaction pattern as DrishtiVia's
// hero/about CTA buttons: label slides up on hover, circular icon rotates.
export function PillButton({
  label,
  href,
  onClick,
  variant = "brand", // "brand" | "dark" | "light"
  className = "",
}) {
  const variants = {
    brand: "bg-[var(--color-brand)] text-white",
    dark: "bg-[var(--color-ink-900)] text-white",
    light: "bg-white text-[var(--color-ink-900)]",
  };
  const iconBg = variant === "light" ? "bg-[var(--color-ink-900)]" : "bg-white";
  const iconColor =
    variant === "brand" ? "text-[var(--color-brand)]" : variant === "dark" ? "text-[var(--color-ink-900)]" : "text-white";

  const Tag = href ? "a" : "button";

  return (
    <Tag
      href={href}
      onClick={onClick}
      className={`group inline-flex items-center gap-3 overflow-hidden rounded-full py-2 pl-5 pr-2 text-[13px] font-medium no-underline transition-colors duration-300 ${variants[variant]} ${className}`}
    >
      <span className="overflow-hidden" style={{ height: "20px" }}>
        <span className="flex flex-col transition-transform duration-500 ease-[cubic-bezier(0.25,0.1,0.25,1)] group-hover:-translate-y-1/2">
          <span className="block" style={{ lineHeight: "20px" }}>{label}</span>
          <span className="block" style={{ lineHeight: "20px" }}>{label}</span>
        </span>
      </span>
      <span
        className={`flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full transition-transform duration-500 ease-[cubic-bezier(0.25,0.1,0.25,1)] group-hover:-rotate-45 ${iconBg}`}
      >
        <ArrowRight size={13} className={iconColor} />
      </span>
    </Tag>
  );
}
