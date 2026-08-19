"""
Build a trimmed feature dataframe from data/rm_price_data.csv for forecasting
aluminium_price and pvc_resin_price.

Trimmed down from an initial 32-feature set (see correlation_analysis.py) to
just the (predictor, lag) pairs that actually ranked as the strongest drivers,
plus one 3-month rolling average per predictor to capture trend:

  - crude_oil_price (same-month)  - top driver for both targets, esp. PVC
  - crude_oil_price_lag1          - strongest single PVC driver (+0.796)
  - crude_oil_price_roll3         - trend version of crude oil
  - usd_inr_rate (same-month)     - top driver for aluminium
  - usd_inr_rate_lag6             - stays strong for aluminium at distance
  - usd_inr_rate_roll3            - trend version of USD/INR
  - energy_price_index (same-month) + roll3 - added after correlation_analysis.py
    showed a 0.674 same-month correlation with aluminium_price (second only to
    crude oil), consistent with the case study listing energy prices as an
    aluminium driver (smelting is energy-intensive). Engineered here for both
    targets, but forecast_model.py's RIDGE_EXTRA_FEATURES only wires it into
    the ALUMINIUM Ridge model - PVC's own correlation with it (0.553) is
    weaker than PVC's existing crude-oil-driven features, so it's not added
    there. Note: energy_price_index correlates 0.899 with usd_inr_rate -
    Ridge's L2 penalty handles that collinearity reasonably, but don't
    over-read the split between their individual coefficients.

freight_index is dropped entirely as a model input - it had the weakest
correlation with both targets at every lag in correlation_analysis.py. It
stays in the causal knowledge graph as a qualitative driver, just not as a
regression feature.

crude_oil_price_inr_adjusted (crude_oil_price * usd_inr_rate) is computed but
NOT included in the default feature set - it hasn't been shown to beat raw
crude_oil_price, so we don't keep both by default. It's left in the output
purely as an available ablation for later testing.

demand_index (FRED INDPRO, US Industrial Production: Total Index) was tested
via correlation_analysis.py and NOT included: its strongest correlation is
same-month with aluminium_price at only 0.330, and 0.242 with pvc_resin_price
- both well below the 0.5 bar used for every other feature here. Per the case
study's explicit allowance to "add or drop indicators with justification":
industrial production is a broad, economy-wide demand proxy, while aluminium
and PVC resin prices in this window are shown (in correlation_analysis.py and
the causal knowledge graph) to be driven far more by feedstock/input costs
(crude oil, energy, currency) than by aggregate domestic demand - so it's
dropped rather than forced in.

shock_zscore_prior is a numeric feature (not just an alert): the largest
|z-score| across crude_oil_price, usd_inr_rate, and energy_price_index's
month-over-month move in the PRIOR month, reusing risk_alerts.py's own
anomaly z-score (compute_zscore_series) so this feature and the standalone
alert layer always agree on what counts as unusual. This is what actually
answers the case study's "model inputs to include... price surge/shock
events" requirement as a regression input - risk_alerts.py itself stays
unchanged and keeps serving the dashboard's separate warning banner.
freight_index is excluded from this shock calculation since it isn't itself
a Ridge feature for either target.

Saves data/rm_features.csv.

Run with:
    python src/feature_engineering.py
"""

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import risk_alerts  # noqa: E402 - reuse its z-score logic for shock_zscore_prior

DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "rm_price_data.csv"
)
OUTPUT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "rm_features.csv"
)

TARGETS = ["aluminium_price", "pvc_resin_price"]

# predictor -> which lags / rolling windows to include, based on the
# strongest (predictor, lag) pairs found in correlation_analysis.py
TRIMMED_PREDICTOR_CONFIG = {
    "crude_oil_price": {"lags": [1], "rolling": [3]},
    "usd_inr_rate": {"lags": [6], "rolling": [3]},
    "energy_price_index": {"lags": [], "rolling": [3]},
}

# Drivers whose month-over-month move feeds the shock_zscore_prior feature -
# the model-input drivers already tracked, not freight_index (not itself a
# Ridge feature) and not demand_index (excluded below - correlation too weak).
SHOCK_DRIVERS = ["crude_oil_price", "usd_inr_rate", "energy_price_index"]

DROPPED_NOTE = (
    "Dropped: freight_index (weakest correlation with both targets at every lag), "
    "crude_oil_price_inr_adjusted (not shown to beat raw crude_oil_price - kept "
    "available as an ablation, not selected by default), demand_index / FRED INDPRO "
    "(tested - max correlation 0.330 with aluminium_price, 0.242 with pvc_resin_price, "
    "below the 0.5 bar used for every other feature - see module docstring for justification)"
)


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, index_col=0, parse_dates=True)
    df.index.name = "date"
    return df


def add_inr_adjusted_crude_ablation(df: pd.DataFrame) -> None:
    """Computed for anyone who wants to test it later, not selected by default."""
    df["crude_oil_price_inr_adjusted"] = df["crude_oil_price"] * df["usd_inr_rate"]


def add_shock_feature(df: pd.DataFrame) -> None:
    """
    shock_zscore_prior[t] = max(|z-score|) across SHOCK_DRIVERS' move during
    month t-1, using risk_alerts.py's own anomaly z-score. shift(1) makes
    this the PRIOR month's shock intensity - known before month t - not a
    same-month value that would leak information.
    """
    driver_zscores = pd.DataFrame(
        {driver: risk_alerts.compute_zscore_series(df, driver).abs() for driver in SHOCK_DRIVERS}
    )
    shock_intensity = driver_zscores.max(axis=1)
    df["shock_zscore_prior"] = shock_intensity.shift(1).reindex(df.index)


def build_features() -> tuple:
    df = load_data()
    add_inr_adjusted_crude_ablation(df)
    add_shock_feature(df)

    feature_columns = ["shock_zscore_prior"]
    for predictor, config in TRIMMED_PREDICTOR_CONFIG.items():
        feature_columns.append(predictor)  # same-month / raw value

        for lag in config["lags"]:
            col = f"{predictor}_lag{lag}"
            df[col] = df[predictor].shift(lag)
            feature_columns.append(col)

        for window in config["rolling"]:
            col = f"{predictor}_roll{window}"
            df[col] = df[predictor].rolling(window).mean()
            feature_columns.append(col)

    result = df[TARGETS + feature_columns].dropna()
    return result, feature_columns


def print_overfitting_check(df: pd.DataFrame, n_predictor_features: int) -> None:
    n_rows = len(df)
    ratio = n_predictor_features / n_rows

    print(f"\nRows after dropping incomplete lag/rolling history: {n_rows}")
    print(f"Predictor feature columns (excludes the 2 targets): {n_predictor_features}")
    print(f"Feature-to-row ratio: {ratio:.3f} ({n_predictor_features} features / {n_rows} rows)")

    if ratio >= 0.3:
        level = "HIGH"
    elif ratio >= 0.15:
        level = "MODERATE"
    else:
        level = "LOW"
    print(f"Overfitting risk: {level}")


def main():
    result, feature_columns = build_features()

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    result.to_csv(OUTPUT_PATH)
    print(f"Saved {OUTPUT_PATH}")

    print(f"\nTrimmed feature list ({len(feature_columns)} predictor columns):")
    for col in feature_columns:
        print(f"  - {col}")
    print(f"\n{DROPPED_NOTE}")

    print(f"\nTarget columns (carried through, not features): {TARGETS}")
    print(f"Output shape: {result.shape[0]} rows x {result.shape[1]} columns "
          f"({result.shape[1] - len(TARGETS)} features + {len(TARGETS)} targets)")

    print_overfitting_check(result, len(feature_columns))


if __name__ == "__main__":
    main()
