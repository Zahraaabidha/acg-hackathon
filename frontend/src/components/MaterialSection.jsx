import { Card } from "./Card";
import { ForecastChart } from "./ForecastChart";
import { ChartLegend } from "./ChartLegend";
import { NarrativeCallout } from "./NarrativeCallout";
import { SignalTable } from "./SignalTable";
import { ModelDetails } from "./ModelDetails";

export function MaterialSection({ material, shifted, id }) {
  const nextMonth = material.forecast[0];

  return (
    <Card
      id={id}
      eyebrow="6-Month Forecast"
      title={material.label}
      subtitle="Ridge regression with 90% prediction interval"
      action={
        <span
          className="inline-flex h-2.5 w-2.5 rounded-full"
          style={{ backgroundColor: material.color }}
          aria-hidden
        />
      }
    >
      <ForecastChart
        history={material.history}
        forecast={material.forecast}
        color={material.color}
        shifted={shifted}
      />
      <ChartLegend color={material.color} showWhatIf={Boolean(shifted)} />

      <div className="mt-5">
        <NarrativeCallout narrative={nextMonth?.narrative} color={material.color} />
      </div>

      <div className="mt-5">
        <SignalTable forecast={material.forecast} />
      </div>

      <ModelDetails accuracy={material.accuracy} featureImportances={material.featureImportances} />
    </Card>
  );
}
