"""
Risk/shock alert layer: flag months where a driver (crude_oil_price,
usd_inr_rate, freight_index) moves unusually far from its own typical
month-over-month change. This is a simple statistical anomaly threshold, not
a learned one, so it's easy to explain in the pitch: "this driver moved more
than 1.5 standard deviations from its own historical average move."

These alerts are independent of the prediction interval in
forecast_model.py/procurement_signal.py - a forecast can have a narrow,
"high confidence" interval and still be standing on a shock month for one of
its own inputs, which the confidence interval alone wouldn't catch.

Run against the FULL historical dataset (not just the recent test window),
so it validates against real events - the 2020 COVID crude collapse and the
2021-22 commodity surge both show up.

Saves output/risk_alerts.csv.

Run with:
    python src/risk_alerts.py
"""

import os

import pandas as pd

RAW_PRICES_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "rm_price_data.csv"
)
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")

DRIVERS = ["crude_oil_price", "usd_inr_rate", "freight_index", "energy_price_index"]
Z_THRESHOLD = 1.5  # flag a month if its move is > 1.5 std devs from that driver's own average move

# Which price targets each driver feeds, per knowledge_graph.py and
# forecast_model.py's RIDGE_EXTRA_FEATURES. crude_oil feeds both chains,
# usd_inr_rate and energy_price_index are aluminium-specific model features,
# freight_index is qualitative-only for both (not a model feature) but still
# worth flagging as market context when it moves unusually.
AFFECTED_TARGETS = {
    "crude_oil_price": ["aluminium_price", "pvc_resin_price"],
    "usd_inr_rate": ["aluminium_price"],
    "freight_index": ["aluminium_price", "pvc_resin_price"],
    "energy_price_index": ["aluminium_price"],
}


def load_raw_prices() -> pd.DataFrame:
    df = pd.read_csv(RAW_PRICES_PATH, index_col=0, parse_dates=True)
    df.index.name = "date"
    return df


def compute_zscore_series(raw: pd.DataFrame, driver: str) -> pd.Series:
    """
    z-score of EVERY month's move (not just the ones that cross a threshold):
    how many std devs that month's % move is from the driver's own average
    move (mean/std computed over its full history) - so a normally volatile
    driver like freight needs a bigger move to register as unusual than a
    normally calm one like USD/INR.

    Exposed standalone (not just inlined in find_alerts_for_driver) so
    feature_engineering.py can reuse the exact same anomaly measure to build
    a shock-intensity model feature - the alert layer and the model feature
    are guaranteed to agree on what "unusual" means.
    """
    pct_change = (raw[driver].pct_change() * 100).dropna()
    mean_move = pct_change.mean()
    std_move = pct_change.std()
    return (pct_change - mean_move) / std_move


def find_alerts_for_driver(raw: pd.DataFrame, driver: str, z_threshold: float) -> pd.DataFrame:
    pct_change = (raw[driver].pct_change() * 100).dropna()
    z_scores = compute_zscore_series(raw, driver)
    flagged = z_scores[z_scores.abs() > z_threshold]

    rows = []
    for date, z in flagged.items():
        rows.append(
            {
                "month": date.strftime("%Y-%m"),
                "driver": driver,
                "pct_change": round(pct_change.loc[date], 2),
                "z_score": round(z, 2),
                "affected_targets": ", ".join(AFFECTED_TARGETS[driver]),
            }
        )
    return pd.DataFrame(rows)


def print_alert(row: pd.Series) -> None:
    targets = row["affected_targets"]
    plural = "s" if "," in targets else ""
    print(
        f"ALERT: {row['driver']} moved {row['pct_change']:+.0f}% in {row['month']} - unusual "
        f"volatility (z={row['z_score']:+.2f}), treat {targets} forecast{plural} with added "
        f"caution regardless of its confidence interval."
    )


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    raw = load_raw_prices()

    all_alerts = [find_alerts_for_driver(raw, driver, Z_THRESHOLD) for driver in DRIVERS]
    alerts_df = pd.concat(all_alerts, ignore_index=True).sort_values("month").reset_index(drop=True)

    print(f"{'=' * 70}\nRisk/shock alerts ({Z_THRESHOLD} std-dev threshold, full history "
          f"{raw.index.min().strftime('%Y-%m')} to {raw.index.max().strftime('%Y-%m')})\n{'=' * 70}")
    if alerts_df.empty:
        print("No months flagged.")
    else:
        for _, row in alerts_df.iterrows():
            print_alert(row)

    out_path = os.path.join(OUTPUT_DIR, "risk_alerts.csv")
    alerts_df.to_csv(out_path, index=False)
    print(f"\nSaved {out_path}")

    total_driver_months = len(raw) * len(DRIVERS)
    print(
        f"\n{len(alerts_df)} driver-months flagged out of {total_driver_months} total "
        f"({len(raw)} months x {len(DRIVERS)} drivers) - "
        f"{len(alerts_df) / total_driver_months:.1%} flag rate."
    )


if __name__ == "__main__":
    main()
