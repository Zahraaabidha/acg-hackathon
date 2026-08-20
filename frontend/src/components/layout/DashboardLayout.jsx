import { useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { Sliders } from "lucide-react";
import { useDashboardData } from "../../hooks/useDashboardData";
import { DashboardSidebar } from "./DashboardSidebar";
import { FullScreenMessage } from "../FullScreenMessage";

const PAGE_TITLES = {
  "/dashboard": "Overview",
  "/dashboard/aluminium": "Aluminium",
  "/dashboard/pvc": "PVC Resin",
  "/dashboard/graph": "Driver Graph",
  "/dashboard/risk": "Risk Alerts",
};

// Shared shell for every dashboard sub-page: sidebar + sticky top bar. Data
// is fetched ONCE here and the what-if sliders live here too, so both persist
// as you navigate between pages - each page reads them via useOutletContext.
export function DashboardLayout() {
  const { data, error } = useDashboardData();
  const [crudePct, setCrudePct] = useState(0);
  const [fxPct, setFxPct] = useState(0);
  const { pathname } = useLocation();
  const title = PAGE_TITLES[pathname] ?? "Dashboard";

  if (error) {
    return (
      <FullScreenMessage
        title="Couldn't load dashboard data"
        detail={error}
        hint="python src/export_dashboard_data.py"
      />
    );
  }

  if (!data) {
    return <FullScreenMessage title="Loading dashboard…" />;
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--color-page)]">
      <DashboardSidebar dataAsOf={data.dataAsOf} />

      <main className="flex min-w-0 flex-1 flex-col overflow-y-auto">
        <header
          className="sticky top-0 z-30 flex items-center justify-between gap-4 border-b border-[var(--color-hairline)] px-8 py-4"
          style={{ background: "rgba(248,249,250,0.9)", backdropFilter: "blur(12px)" }}
        >
          <p className="text-[13px] font-medium text-[var(--color-ink-secondary)]">{title}</p>
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-white ring-1 ring-[var(--color-hairline)]">
            <Sliders size={13} className="text-[var(--color-ink-secondary)]" />
          </span>
        </header>

        <div className="px-8 py-6">
          <Outlet context={{ data, crudePct, fxPct, setCrudePct, setFxPct }} />
        </div>
      </main>
    </div>
  );
}
