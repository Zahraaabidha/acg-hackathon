import { useOutletContext } from "react-router-dom";
import { RiskAlerts } from "../../components/RiskAlerts";

export default function RiskPage() {
  const { data } = useOutletContext();

  return (
    <div className="space-y-6 pb-16">
      <RiskAlerts riskAlerts={data.riskAlerts} covidExample={data.covidExample} />
    </div>
  );
}
