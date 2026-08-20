import { Route, Routes } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import { DashboardLayout } from "./components/layout/DashboardLayout";
import OverviewPage from "./pages/dashboard/OverviewPage";
import AluminiumPage from "./pages/dashboard/AluminiumPage";
import PvcPage from "./pages/dashboard/PvcPage";
import GraphPage from "./pages/dashboard/GraphPage";
import RiskPage from "./pages/dashboard/RiskPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/dashboard" element={<DashboardLayout />}>
        <Route index element={<OverviewPage />} />
        <Route path="aluminium" element={<AluminiumPage />} />
        <Route path="pvc" element={<PvcPage />} />
        <Route path="graph" element={<GraphPage />} />
        <Route path="risk" element={<RiskPage />} />
      </Route>
    </Routes>
  );
}
