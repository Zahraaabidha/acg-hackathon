"""
Export ONE clean JSON file for the React frontend: frontend/public/data.json.

This is the single data source for the static React app - no backend server,
no live API calls from the browser. Everything here is either read straight
from existing pipeline outputs (risk_alerts.csv, forecast_narratives.txt) or
refit using the EXACT same functions procurement_signal.py and
forecast_model.py already use, so the JSON's numbers are guaranteed to match
what those scripts print/save - this script doesn't invent a separate model.

Two Ridge fits are exported per target, deliberately kept distinct:
  - "feature_importances": standardized coefficients from the TRAIN/TEST
    evaluation split (forecast_model.py's methodology) - answers "why do
    these features matter" with the same numbers already validated there.
  - "what_if": raw-space sensitivities (d target / d raw feature) from the
    FULL-DATA deployed model (procurement_signal.py's fit_ridge_full) - the
    model that actually produced the shown forecast, used for the
    client-side what-if slider recomputation in the React app.

Run with:
    python src/export_dashboard_data.py
"""

import json
import os
import sys
from datetime import datetime, timezone

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from forecast_model import (  # noqa: E402
    BASE_FEATURE_COLUMNS,
    RIDGE_EXTRA_FEATURES,
    TEST_SIZE,
    add_aluminium_lag_features,
    compute_directional_accuracy,
    compute_metrics,
    fit_naive_baseline,
    fit_ridge,
    time_split,
)
from knowledge_graph import build_graph  # noqa: E402
from procurement_signal import (  # noqa: E402
    MATERIAL_COST_SHARE,
    MATERIAL_LABELS,
    RM_COST_SHARE_TOTAL,
    TARGETS,
    build_signal_table,
    compute_confidence_threshold,
    compute_cost_exposure,
    fit_ridge_full,
    forecast_aluminium,
    forecast_pvc,
    get_ridge_test_predictions,
    load_features,
    load_raw_prices,
)

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")
FRONTEND_DATA_PATH = os.path.join(ROOT_DIR, "frontend", "public", "data.json")

TRAILING_MONTHS = 6
BAND_PCT = 0.03
HISTORY_MONTHS = 12  # trailing actual months of price history included for chart context
COVID_WINDOW = ["2020-03", "2020-04", "2020-05", "2020-06"]  # validation example, see risk_alerts.py

# Node colors chosen to be visually distinct from the two material colors
# (aluminium=blue, PVC=orange - see MATERIAL_COLORS) so drivers never get
# confused with targets in the graph. freight_index uses the muted/ink gray
# since it's qualitative-only (not a model feature), not a categorical hue.
MATERIAL_COLORS = {
    "aluminium_price": "#2a78d6",
    "pvc_resin_price": "#eb6834",
}
DRIVER_COLORS = {
    "crude_oil_price": "#4a3aa7",
    "usd_inr_rate": "#1baf7a",
    "energy_price_index": "#e87ba4",
    "freight_index": "#898781",
}


def node_color(node_name: str) -> str:
    if node_name in MATERIAL_COLORS:
        return MATERIAL_COLORS[node_name]
    return DRIVER_COLORS.get(node_name, "#898781")


def build_knowledge_graph_json() -> dict:
    graph = build_graph()
    nodes = [
        {
            "id": name,
            "category": data["category"],
            "isTarget": data["category"] == "target" or name in MATERIAL_COLORS,
            "color": node_color(name),
        }
        for name, data in graph.nodes(data=True)
    ]
    edges = [
        {
            "source": source,
            "target": target,
            "correlation": data["correlation"],
            "lagMonths": data["lag_months"],
            "modelInput": data["model_input"],
            "relationship": data["relationship"],
        }
        for source, target, data in graph.edges(data=True)
    ]
    return {"nodes": nodes, "edges": edges}


def get_eval_feature_importances(df_features: pd.DataFrame, target: str) -> tuple:
    """
    Standardized Ridge coefficients + test-set accuracy from the SAME
    train/test split forecast_model.py evaluates on. Also computes the naive
    baseline for the same test window, for an honest side-by-side.
    """
    feature_columns = BASE_FEATURE_COLUMNS + RIDGE_EXTRA_FEATURES[target]
    X = df_features[feature_columns]
    y = df_features[target]

    X_train, X_test = time_split(X, TEST_SIZE)
    y_train, y_test = time_split(y, TEST_SIZE)
    y_pred, coefficients, _alpha = fit_ridge(X_train, y_train, X_test)

    y_prev = y.shift(1).loc[y_test.index].values
    naive_pred = fit_naive_baseline(y, y_test.index)

    ridge_metrics = compute_metrics(y_test, y_pred)
    ridge_metrics["directionalAccuracy"] = compute_directional_accuracy(y_test, y_pred, y_prev)
    naive_metrics = compute_metrics(y_test, naive_pred)
    naive_metrics["directionalAccuracy"] = compute_directional_accuracy(y_test, naive_pred, y_prev)

    importances = [
        {"feature": name, "coefficient": round(float(coef), 3)} for name, coef in coefficients.items()
    ]
    accuracy = {
        "ridge": {k: round(float(v), 3) for k, v in ridge_metrics.items()},
        "naive": {k: round(float(v), 3) for k, v in naive_metrics.items()},
    }
    return importances, accuracy


def get_what_if_inputs(df_features: pd.DataFrame, raw: pd.DataFrame, target: str) -> dict:
    """
    Raw-space sensitivity (d target / d raw feature) for the SAME-MONTH
    crude_oil_price and usd_inr_rate columns, from the actual DEPLOYED
    full-data model (matches procurement_signal.py exactly). Ridge is fit on
    standardized features, so the raw-space slope is coef_scaled / scale -
    the partial derivative of price w.r.t. that raw input, holding the
    other (lag/rolling) features fixed. This is what the React what-if
    sliders use for a simple, honest client-side linear recomputation - it
    only perturbs the same-month value, not the historical lag/rolling
    context, which a slider has no business rewriting.
    """
    feature_columns = BASE_FEATURE_COLUMNS + RIDGE_EXTRA_FEATURES[target]
    X = df_features[feature_columns]
    y = df_features[target]
    scaler, model = fit_ridge_full(X, y)

    result = {
        "baseCrudeOilPrice": round(float(raw["crude_oil_price"].iloc[-1]), 2),
        "baseUsdInrRate": round(float(raw["usd_inr_rate"].iloc[-1]), 2),
    }
    for feature_name, key in [("crude_oil_price", "crudeOilRawCoefficient"), ("usd_inr_rate", "usdInrRawCoefficient")]:
        if feature_name in feature_columns:
            idx = feature_columns.index(feature_name)
            result[key] = round(float(model.coef_[idx] / scaler.scale_[idx]), 4)
        else:
            result[key] = 0.0
    return result


def get_forecast_and_signal(df_features: pd.DataFrame, raw: pd.DataFrame, target: str) -> tuple:
    """Same methodology as procurement_signal.py's run_for_target() - forecast + interval + confidence + recommendation."""
    feature_columns = BASE_FEATURE_COLUMNS + RIDGE_EXTRA_FEATURES[target]
    X = df_features[feature_columns]
    y = df_features[target]
    scaler, model = fit_ridge_full(X, y)

    y_test, _ridge_test_pred, residual_std = get_ridge_test_predictions(df_features, target)
    confidence_threshold = compute_confidence_threshold(y_test, residual_std)

    forecast = forecast_aluminium(raw, scaler, model) if target == "aluminium_price" else forecast_pvc(raw, scaler, model)
    table = build_signal_table(
        forecast, raw[target], target, TRAILING_MONTHS, BAND_PCT, residual_std, confidence_threshold
    )
    cost_exposure = compute_cost_exposure(table, target, TRAILING_MONTHS)
    return table, cost_exposure


def get_history(raw: pd.DataFrame, target: str) -> list:
    recent = raw[target].iloc[-HISTORY_MONTHS:]
    return [{"month": date.strftime("%Y-%m"), "price": round(float(value), 2)} for date, value in recent.items()]


def load_narratives_by_month(target_label: str) -> dict:
    path = os.path.join(OUTPUT_DIR, "forecast_narratives.txt")
    try:
        with open(path, "r", encoding="utf-8") as f:
            paragraphs = [p.strip() for p in f.read().split("\n\n") if p.strip()]
    except FileNotFoundError:
        return {}

    by_month = {}
    for paragraph in paragraphs:
        if not paragraph.startswith(target_label):
            continue
        # narratives read "... for 2026-09." - pull the YYYY-MM token out.
        marker = " for "
        if marker in paragraph:
            after = paragraph.split(marker, 1)[1]
            month = after.split(".", 1)[0].strip()
            by_month[month] = paragraph
    return by_month


def load_risk_alerts() -> list:
    path = os.path.join(OUTPUT_DIR, "risk_alerts.csv")
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        return []
    return [
        {
            "month": row.month,
            "driver": row.driver,
            "pctChange": round(float(row.pct_change), 2),
            "zScore": round(float(row.z_score), 2),
            "affectedTargets": [t.strip() for t in row.affected_targets.split(",")],
        }
        for row in df.itertuples()
    ]


def main():
    os.makedirs(os.path.dirname(FRONTEND_DATA_PATH), exist_ok=True)

    df_features = load_features()
    df_features = add_aluminium_lag_features(df_features)
    raw = load_raw_prices()

    all_risk_alerts = load_risk_alerts()
    covid_example = [a for a in all_risk_alerts if a["month"] in COVID_WINDOW]

    materials = {}
    for target in TARGETS:
        table, cost_exposure = get_forecast_and_signal(df_features, raw, target)
        importances, accuracy = get_eval_feature_importances(df_features, target)
        what_if = get_what_if_inputs(df_features, raw, target)
        narratives = load_narratives_by_month(MATERIAL_LABELS[target])

        forecast_rows = []
        for _, row in table.iterrows():
            forecast_rows.append(
                {
                    "month": row["month"],
                    "forecastedPrice": row["forecasted_price"],
                    "intervalLow": row["interval_low"],
                    "intervalHigh": row["interval_high"],
                    "trailingAvg": row[f"trailing_{TRAILING_MONTHS}mo_avg"],
                    "recommendation": row["recommendation"],
                    "confidence": row["confidence"],
                    "narrative": narratives.get(row["month"]),
                }
            )

        materials[target] = {
            "key": target,
            "label": MATERIAL_LABELS[target],
            "color": MATERIAL_COLORS[target],
            "history": get_history(raw, target),
            "forecast": forecast_rows,
            "featureImportances": importances,
            "accuracy": accuracy,
            "whatIf": what_if,
            "costExposure": [
                {
                    "month": row["month"],
                    "priceChangePct": row["price_change_pct"],
                    "costBaseShiftPct": row["cost_base_shift_pct"],
                }
                for _, row in cost_exposure.iterrows()
            ],
        }

    data = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "dataAsOf": raw.index.max().strftime("%Y-%m"),
        "materials": materials,
        "knowledgeGraph": build_knowledge_graph_json(),
        "riskAlerts": all_risk_alerts,
        "covidExample": covid_example,
        "costExposureAssumptions": {
            "rmCostShareTotal": RM_COST_SHARE_TOTAL,
            "materialCostShare": MATERIAL_COST_SHARE,
        },
    }

    with open(FRONTEND_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Saved {FRONTEND_DATA_PATH}")
    print(f"Data as of: {data['dataAsOf']}")
    for target in TARGETS:
        print(f"  {MATERIAL_LABELS[target]}: {len(materials[target]['forecast'])} forecasted months, "
              f"{len(materials[target]['featureImportances'])} features")
    print(f"Risk alerts: {len(all_risk_alerts)} total, {len(covid_example)} in the COVID validation window")


if __name__ == "__main__":
    main()
