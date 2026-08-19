"""
Auto-generated forecast narratives: stitch together the forecast + confidence
from procurement_signal.py, the top 2 causal drivers from knowledge_graph.py,
and any active risk_alerts.py alert for that month, into one plain-English
paragraph per forecasted month - ready to paste straight into slide notes.

Driver ranking note: "top drivers" are read from knowledge_graph.py's
get_model_input_features(), which ranks by the real correlations from
correlation_analysis.py - the same drivers actually feeding the Ridge model
(see forecast_model.py's RIDGE_EXTRA_FEATURES). This was checked against the
retrained model's own coefficient ranking and they agree (crude_oil_price and
energy_price_index are aluminium's two strongest drivers by both measures),
so the graph's correlation-based phrasing is accurate and reads better in a
sentence than a raw standardized-coefficient value would.

Risk alert note: forecasted months hold crude_oil_price/usd_inr_rate/
energy_price_index flat at their last observed value (see
procurement_signal.py's module docstring), so by construction no
risk_alerts.py shock can ever fire for a future month - a flat driver never
registers as an anomalous move. Every forecasted-month narrative will
therefore read "No unusual driver volatility detected this month." That's an
honest limitation of the flat-forward assumption, not a bug - stated here so
it isn't mistaken for the alert layer silently failing.

Saves output/forecast_narratives.txt.

Run with:
    python src/narrative_generator.py
"""

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import risk_alerts  # noqa: E402
from forecast_model import add_aluminium_lag_features  # noqa: E402
from knowledge_graph import build_graph, get_model_input_features  # noqa: E402
from procurement_signal import (  # noqa: E402
    MATERIAL_LABELS,
    TARGETS,
    load_features,
    load_raw_prices,
    run_for_target,
)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
TRAILING_MONTHS = 6
BAND_PCT = 0.03
MAX_DRIVERS = 2

DRIVER_DISPLAY_NAMES = {
    "crude_oil_price": "crude oil",
    "usd_inr_rate": "the USD/INR exchange rate",
    "energy_price_index": "energy prices",
    "freight_index": "freight rates",
}


def _driver_phrase(name: str, correlation: float, lag_months: int) -> str:
    display = DRIVER_DISPLAY_NAMES.get(name, name)
    if lag_months:
        return f"{display} (correlation {correlation:.2f}, effect persists to a {lag_months}-month lag)"
    return f"{display} (same-month correlation {correlation:.2f})"


def generate_narrative(
    target: str,
    month: str,
    forecast_value: float,
    confidence: str,
    top_drivers: list,
    risk_alert: str = None,
) -> str:
    """
    top_drivers: list of (driver_name, correlation, lag_months) tuples, e.g.
        from knowledge_graph.get_model_input_features(graph, target).
    risk_alert: an active alert sentence for this month, or None.
    """
    material = MATERIAL_LABELS.get(target, target)
    confidence_phrase = "high confidence" if confidence == "High" else "low confidence - monitor closely"

    if not top_drivers:
        driver_sentence = "No dominant upstream driver was identified for this forecast."
    else:
        phrases = [_driver_phrase(name, corr, lag) for name, corr, lag in top_drivers[:MAX_DRIVERS]]
        if len(phrases) == 1:
            driver_sentence = f"This is primarily driven by {phrases[0]}."
        else:
            driver_sentence = f"This is primarily driven by {phrases[0]} and {phrases[1]}."

    risk_sentence = risk_alert if risk_alert else "No unusual driver volatility detected this month."

    return (
        f"{material} is forecast at {forecast_value:,.0f} ({confidence_phrase}) for {month}. "
        f"{driver_sentence} {risk_sentence}"
    )


def build_top_drivers(graph, target: str) -> list:
    """Top MAX_DRIVERS model-input drivers for target, ranked by correlation (no cutoff -
    the 0.65 feature-selection threshold is main.py's job; this is descriptive context)."""
    return get_model_input_features(graph, target, min_correlation=0.0)[:MAX_DRIVERS]


def get_historical_alerts() -> pd.DataFrame:
    """Real risk_alerts.py alerts over historical data - reused, not recomputed."""
    raw = risk_alerts.load_raw_prices()
    frames = [
        risk_alerts.find_alerts_for_driver(raw, driver, risk_alerts.Z_THRESHOLD)
        for driver in risk_alerts.DRIVERS
    ]
    return pd.concat(frames, ignore_index=True)


def lookup_alert_for_month(alerts_df: pd.DataFrame, month: str) -> str:
    matches = alerts_df[alerts_df["month"] == month]
    if matches.empty:
        return None
    parts = [f"{row.driver} moved {row.pct_change:+.0f}%" for row in matches.itertuples()]
    return (
        f"Note: {'; '.join(parts)} - unusual driver volatility flagged this month, "
        f"treat this forecast with added caution."
    )


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    graph = build_graph()

    df_features = load_features()
    df_features = add_aluminium_lag_features(df_features)
    raw = load_raw_prices()
    historical_alerts = get_historical_alerts()

    narratives = []
    for target in TARGETS:
        table = run_for_target(df_features, raw, target, TRAILING_MONTHS, BAND_PCT)
        top_drivers = build_top_drivers(graph, target)

        print(f"\n{'=' * 70}\n{MATERIAL_LABELS[target]} forecast narratives\n{'=' * 70}")
        for row in table.itertuples():
            alert = lookup_alert_for_month(historical_alerts, row.month)
            narrative = generate_narrative(
                target, row.month, row.forecasted_price, row.confidence, top_drivers, alert
            )
            narratives.append(narrative)
            print(narrative)

    out_path = os.path.join(OUTPUT_DIR, "forecast_narratives.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(narratives) + "\n")
    print(f"\nSaved {len(narratives)} narratives to {out_path}")


if __name__ == "__main__":
    main()
