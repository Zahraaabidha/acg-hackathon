import { useState } from "react";
import { Link, NavLink } from "react-router-dom";
import { AlertTriangle, ChevronLeft, ChevronRight, LayoutGrid, Layers, Share2 } from "lucide-react";

const NAV_LINKS = [
  { label: "Overview", to: "/dashboard", icon: LayoutGrid, end: true },
  { label: "Aluminium", to: "/dashboard/aluminium", icon: Layers },
  { label: "PVC Resin", to: "/dashboard/pvc", icon: Layers },
  { label: "Driver Graph", to: "/dashboard/graph", icon: Share2 },
  { label: "Risk Alerts", to: "/dashboard/risk", icon: AlertTriangle },
];

export function DashboardSidebar({ dataAsOf }) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={`flex h-full shrink-0 flex-col border-r border-[var(--color-hairline)] bg-white transition-all duration-300 ${collapsed ? "w-[68px]" : "w-[220px]"}`}
    >
      <div className="flex items-center gap-2.5 border-b border-[var(--color-hairline)] px-4 py-5">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[3px] bg-[var(--color-ink-900)]">
          <span className="font-display text-[10px] font-bold text-white">AC</span>
        </div>
        {!collapsed && (
          <span className="font-display text-[13px] font-extrabold uppercase tracking-[0.14em] text-[var(--color-ink-900)]">
            Smart Buy
          </span>
        )}
      </div>

      <nav className="flex flex-1 flex-col gap-1 px-2 py-4">
        {!collapsed && <p className="eyebrow mb-1 px-2">Navigation</p>}
        {NAV_LINKS.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.end}
            className={({ isActive }) =>
              `flex items-center gap-2.5 rounded-[4px] px-2.5 py-2 text-[13px] font-medium transition-all ${
                isActive
                  ? "bg-[var(--color-ink-900)] text-white"
                  : "text-[var(--color-ink-secondary)] hover:bg-[var(--color-page)] hover:text-[var(--color-ink-900)]"
              }`
            }
          >
            <link.icon size={16} className="shrink-0" />
            {!collapsed && <span>{link.label}</span>}
          </NavLink>
        ))}
      </nav>

      <div className="flex flex-col gap-2 border-t border-[var(--color-hairline)] px-2 py-4">
        <button
          onClick={() => setCollapsed((c) => !c)}
          className="flex w-full items-center gap-2 rounded-[4px] px-2.5 py-2 text-[12px] text-[var(--color-ink-muted)] transition-all hover:bg-[var(--color-page)] hover:text-[var(--color-ink-900)]"
        >
          {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
          {!collapsed && <span>Collapse</span>}
        </button>
        <Link
          to="/"
          className="flex items-center gap-2 px-2.5 py-2 text-[12px] text-[var(--color-ink-muted)] no-underline hover:text-[var(--color-ink-900)]"
        >
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[var(--color-page)] text-[10px] font-bold text-[var(--color-ink-secondary)]">
            ←
          </span>
          {!collapsed && (
            <div className="min-w-0">
              <p className="truncate text-[12px] font-semibold text-[var(--color-ink-secondary)]">Back to site</p>
              <p className="tabular-nums truncate text-[10px] text-[var(--color-ink-muted)]">Data as of {dataAsOf}</p>
            </div>
          )}
        </Link>
      </div>
    </aside>
  );
}
