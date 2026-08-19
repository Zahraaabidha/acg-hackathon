"""
Procurement decision layer: forecast the next 6 months of aluminium_price and
pvc_resin_price with the winning Ridge models, then classify each month as
"Buy now" / "Wait" / "Neutral / Monitor" against a trailing N-month average.

This is demo/slide output, not just an internal metric - tables and one-line
explanations are printed and saved to /output/ so they can go straight into a
pitch.

Forecasting assumption (stated plainly, not hidden): crude_oil_price,
usd_inr_rate, and energy_price_index have no known future values, so they're
held flat at their last observed value for the forecast horizon. This is a
simplifying assumption, not a claim that oil/FX/energy prices will literally
stay flat - swap in real forward estimates here if you have them. Note this
also means no risk_alerts.py-style shock can ever fire for a future month by
construction, since a flat driver never registers as an anomalous move.

Run with:
    python src/procurement_signal.py
"""

import os
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeCV
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(__file__))
from forecast_model import (  # noqa: E402
    BASE_FEATURE_COLUMNS,
    RIDGE_EXTRA_FEATURES,
    Z_90,
    add_aluminium_lag_features,
    get_ridge_test_predictions,
)

RAW_PRICES_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "rm_price_data.csv"
)
FEATURES_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "rm_features.csv"
)
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")

TARGETS = ["aluminium_price", "pvc_resin_price"]
FORECAST_HORIZON = 6  # months ahead to forecast - matches the case study's "Your Challenge" horizon

MATERIAL_LABELS = {
    "aluminium_price": "Aluminium",
    "pvc_resin_price": "PVC resin",
}


def load_raw_prices() -> pd.DataFrame:
    df = pd.read_csv(RAW_PRICES_PATH, index_col=0, parse_dates=True)
    df.index.name = "date"
    return df


def load_features() -> pd.DataFrame:
    df = pd.read_csv(FEATURES_PATH, index_col=0, parse_dates=True)
    df.index.name = "date"
    return df


SHOCK_DRIVERS = ["crude_oil_price", "usd_inr_rate", "energy_price_index"]


def compute_driver_move_stats(raw: pd.DataFrame, drivers: list) -> dict:
    """
    Fixed (mean_move, std_move) per driver from REAL actual history only -
    used as the shock_zscore_prior denominator for future months too, so a
    flat-forward 0% move is judged against real historical volatility, not
    against a distribution corrupted by the flat-forward assumption itself.
    """
    stats = {}
    for driver in drivers:
        pct_change = (raw[driver].pct_change() * 100).dropna()
        stats[driver] = (pct_change.mean(), pct_change.std())
    return stats


def compute_shock_zscore_prior(series_map: dict, move_stats: dict) -> float:
    """
    Max |z-score| of each driver's most recently COMPLETED month-over-month
    move (the last two entries in each extended series). Call this BEFORE
    appending the current iteration's flat-forward value, so it always
    reflects the PRIOR month's move - for forecast month 1 that's a real
    historical move; for month 2+ it's the move between two flat-forward
    values (~0%, but scored against real historical mean/std, so it isn't
    exactly 0 unless that driver's own average historical move is also 0).
    """
    z_scores = []
    for driver, series in series_map.items():
        prev, prev_prev = series.iloc[-1], series.iloc[-2]
        pct_change = (prev - prev_prev) / prev_prev * 100
        mean_move, std_move = move_stats[driver]
        z_scores.append(abs((pct_change - mean_move) / std_move))
    return max(z_scores)


def fit_ridge_full(X: pd.DataFrame, y: pd.Series) -> tuple:
    """
    Refit the winning Ridge feature set on ALL available history (not just
    the train split used for backtesting) - for actually forecasting unseen
    future months you want the model to see the most recent data too.
    """
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    model = RidgeCV(alphas=[0.1, 1.0, 10.0, 100.0])
    model.fit(X_scaled, y)
    return scaler, model


def forecast_aluminium(raw: pd.DataFrame, scaler, model) -> pd.Series:
    """
    Recursive forecast for aluminium_price, FORECAST_HORIZON months ahead.
    crude_oil_price, usd_inr_rate, and energy_price_index are all held flat
    at their last observed value (see module docstring); aluminium_price_lag1/
    lag3 use the model's own prior forecasts as the horizon advances, since
    Ridge has no built-in memory.
    """
    feature_columns = BASE_FEATURE_COLUMNS + RIDGE_EXTRA_FEATURES["aluminium_price"]

    last_crude = raw["crude_oil_price"].iloc[-1]
    last_fx = raw["usd_inr_rate"].iloc[-1]
    last_energy = raw["energy_price_index"].iloc[-1]
    future_dates = pd.date_range(
        raw.index[-1] + pd.DateOffset(months=1), periods=FORECAST_HORIZON, freq="MS"
    )

    # Extended series we append forecasted values to, so lag1/lag3/roll3 can
    # look back across the actual-history / forecast boundary.
    crude_series = raw["crude_oil_price"].copy()
    fx_series = raw["usd_inr_rate"].copy()
    energy_series = raw["energy_price_index"].copy()
    aluminium_series = raw["aluminium_price"].copy()
    move_stats = compute_driver_move_stats(raw, SHOCK_DRIVERS)

    forecasts = {}
    for date in future_dates:
        shock_prior = compute_shock_zscore_prior(
            {"crude_oil_price": crude_series, "usd_inr_rate": fx_series, "energy_price_index": energy_series},
            move_stats,
        )

        crude_series.loc[date] = last_crude  # flat-forward assumption
        fx_series.loc[date] = last_fx  # flat-forward assumption
        energy_series.loc[date] = last_energy  # flat-forward assumption

        row = {
            "crude_oil_price": crude_series.loc[date],
            "crude_oil_price_lag1": crude_series.shift(1).loc[date],
            "crude_oil_price_roll3": crude_series.rolling(3).mean().loc[date],
            "usd_inr_rate": fx_series.loc[date],
            "usd_inr_rate_lag6": fx_series.shift(6).loc[date],
            "usd_inr_rate_roll3": fx_series.rolling(3).mean().loc[date],
            "energy_price_index": energy_series.loc[date],
            "energy_price_index_roll3": energy_series.rolling(3).mean().loc[date],
            "aluminium_price_lag1": aluminium_series.iloc[-1],
            "aluminium_price_lag3": aluminium_series.iloc[-3],
            "shock_zscore_prior": shock_prior,
        }
        X_future = pd.DataFrame([row], index=[date])[feature_columns]
        X_future_scaled = scaler.transform(X_future)
        prediction = model.predict(X_future_scaled)[0]

        forecasts[date] = prediction
        aluminium_series.loc[date] = prediction  # feeds next iteration's lag1/lag3

    return pd.Series(forecasts)


def forecast_pvc(raw: pd.DataFrame, scaler, model) -> pd.Series:
    """
    6-month forecast for pvc_resin_price - no self-lag, so no target
    recursion needed. Still tracks energy_series purely to compute
    shock_zscore_prior (SHOCK_DRIVERS includes energy_price_index even
    though it isn't itself a PVC feature).
    """
    feature_columns = BASE_FEATURE_COLUMNS + RIDGE_EXTRA_FEATURES["pvc_resin_price"]

    last_crude = raw["crude_oil_price"].iloc[-1]
    last_fx = raw["usd_inr_rate"].iloc[-1]
    last_energy = raw["energy_price_index"].iloc[-1]
    future_dates = pd.date_range(
        raw.index[-1] + pd.DateOffset(months=1), periods=FORECAST_HORIZON, freq="MS"
    )

    crude_series = raw["crude_oil_price"].copy()
    fx_series = raw["usd_inr_rate"].copy()
    energy_series = raw["energy_price_index"].copy()
    move_stats = compute_driver_move_stats(raw, SHOCK_DRIVERS)

    forecasts = {}
    for date in future_dates:
        shock_prior = compute_shock_zscore_prior(
            {"crude_oil_price": crude_series, "usd_inr_rate": fx_series, "energy_price_index": energy_series},
            move_stats,
        )

        crude_series.loc[date] = last_crude
        fx_series.loc[date] = last_fx
        energy_series.loc[date] = last_energy

        row = {
            "crude_oil_price": crude_series.loc[date],
            "crude_oil_price_lag1": crude_series.shift(1).loc[date],
            "crude_oil_price_roll3": crude_series.rolling(3).mean().loc[date],
            "usd_inr_rate": fx_series.loc[date],
            "usd_inr_rate_lag6": fx_series.shift(6).loc[date],
            "usd_inr_rate_roll3": fx_series.rolling(3).mean().loc[date],
            "shock_zscore_prior": shock_prior,
        }
        X_future = pd.DataFrame([row], index=[date])[feature_columns]
        X_future_scaled = scaler.transform(X_future)
        forecasts[date] = model.predict(X_future_scaled)[0]

    return pd.Series(forecasts)


RM_COST_SHARE_TOTAL = 0.70  # ACG's combined aluminium + PVC raw-material cost share of total cost base (case study)

# The case study only gives the COMBINED 70% figure - no aluminium/PVC split
# is provided, so this splits it evenly by default. Tune these two numbers if
# real procurement spend weights become available; they should still sum to
# RM_COST_SHARE_TOTAL.
MATERIAL_COST_SHARE = {
    "aluminium_price": 0.35,
    "pvc_resin_price": 0.35,
}


def compute_cost_exposure(table: pd.DataFrame, target: str, trailing_months: int) -> pd.DataFrame:
    """
    Simple linear pass-through, not a procurement forecast: if a material's
    forecasted price is X% away from its trailing average, and that material
    is S% of ACG's total cost base, a first-order approximation is that total
    RM cost base shifts by X% * S - e.g. a +10% price move on a material
    that's 35% of cost base implies an approximate +3.5% shift in total RM
    cost. No elasticity, substitution, or volume effects are modeled - this
    is a directional sensitivity figure for the pitch.
    """
    avg_col = f"trailing_{trailing_months}mo_avg"
    share = MATERIAL_COST_SHARE[target]

    rows = []
    for _, row in table.iterrows():
        price_change_pct = (row["forecasted_price"] - row[avg_col]) / row[avg_col] * 100
        cost_base_shift_pct = price_change_pct * share
        rows.append(
            {
                "month": row["month"],
                "material": MATERIAL_LABELS[target],
                "price_change_pct": round(price_change_pct, 2),
                "material_cost_share": share,
                "cost_base_shift_pct": round(cost_base_shift_pct, 2),
            }
        )
    return pd.DataFrame(rows)


def print_cost_exposure(exposure_df: pd.DataFrame) -> None:
    for _, row in exposure_df.iterrows():
        print(
            f"  {row['month']}: a {row['price_change_pct']:+.1f}% move in {row['material']} price "
            f"implies an approximate {row['cost_base_shift_pct']:+.2f}% shift in total RM cost base."
        )


def classify_recommendation(forecast_price: float, trailing_avg: float, band_pct: float) -> str:
    pct_diff = (forecast_price - trailing_avg) / trailing_avg
    if pct_diff > band_pct:
        return "Buy now"
    elif pct_diff < -band_pct:
        return "Wait"
    else:
        return "Neutral / Monitor"


def compute_confidence_threshold(y_test: pd.Series, residual_std: float) -> float:
    """
    Historical median RELATIVE interval width (interval width as a % of
    price) over the test-period months - relative, not absolute, so the
    threshold is naturally calibrated to each target's own price scale
    (aluminium's price is ~10x PVC resin's, so an absolute-dollar threshold
    wouldn't transfer between them). This becomes the High/Low confidence
    cutoff applied to future forecasts.
    """
    interval_width = 2 * Z_90 * residual_std
    relative_widths = interval_width / y_test.values
    return float(np.median(relative_widths))


def classify_confidence(forecast_price: float, residual_std: float, threshold: float) -> str:
    interval_width = 2 * Z_90 * residual_std
    relative_width = interval_width / forecast_price
    return "High" if relative_width <= threshold else "Low"


def build_confidence_recommendation(signal: str, confidence: str) -> str:
    """
    Pairs the buy/wait/neutral signal with its confidence. A low-confidence
    month still shows its underlying signal (so nothing is hidden) but is
    explicitly flagged to lean toward monitoring rather than acting on a
    wide-interval directional call.
    """
    if confidence == "High":
        return f"{signal} (high confidence)"
    return f"{signal} (low confidence - monitor)"


def build_signal_table(
    forecast: pd.Series,
    raw_prices: pd.Series,
    target: str,
    trailing_months: int,
    band_pct: float,
    residual_std: float,
    confidence_threshold: float,
) -> pd.DataFrame:
    trailing_avg = raw_prices.iloc[-trailing_months:].mean()

    rows = []
    for date, forecast_price in forecast.items():
        lower = forecast_price - Z_90 * residual_std
        upper = forecast_price + Z_90 * residual_std
        signal = classify_recommendation(forecast_price, trailing_avg, band_pct)
        confidence = classify_confidence(forecast_price, residual_std, confidence_threshold)

        rows.append(
            {
                "month": date.strftime("%Y-%m"),
                "forecasted_price": round(forecast_price, 2),
                "interval_low": round(lower, 2),
                "interval_high": round(upper, 2),
                f"trailing_{trailing_months}mo_avg": round(trailing_avg, 2),
                "recommendation": signal,
                "confidence": confidence,
                "recommendation_detail": build_confidence_recommendation(signal, confidence),
            }
        )
    return pd.DataFrame(rows)


def print_forecast_ranges(table: pd.DataFrame, target: str) -> None:
    """Deck-ready one-line-per-month range format, e.g.
    'aluminium_price Month 1: 3,160 (range: 3,050-3,270)'."""
    for i, row in enumerate(table.itertuples(), start=1):
        print(
            f"  {target} Month {i}: {row.forecasted_price:,.0f} "
            f"(range: {row.interval_low:,.0f}-{row.interval_high:,.0f}) - {row.recommendation_detail}"
        )


def print_explanation(table: pd.DataFrame, target: str, trailing_months: int) -> None:
    material = MATERIAL_LABELS[target]
    avg_col = f"trailing_{trailing_months}mo_avg"
    trailing_avg = table[avg_col].iloc[0]
    avg_forecast = table["forecasted_price"].mean()
    pct_diff = (avg_forecast - trailing_avg) / trailing_avg * 100

    direction = "above" if pct_diff >= 0 else "below"
    buy_count = (table["recommendation"] == "Buy now").sum()
    wait_count = (table["recommendation"] == "Wait").sum()

    if buy_count > wait_count:
        action = "recommend locking in current supply now"
    elif wait_count > buy_count:
        action = "recommend waiting for a better price"
    else:
        action = "no strong signal - monitor closely"

    print(
        f"\n{material} forecasted to be {abs(pct_diff):.0f}% {direction} its "
        f"{trailing_months}-month average over the next {FORECAST_HORIZON} months - {action}."
    )


def run_for_target(
    df_features: pd.DataFrame,
    raw: pd.DataFrame,
    target: str,
    trailing_months: int,
    band_pct: float,
) -> pd.DataFrame:
    feature_columns = BASE_FEATURE_COLUMNS + RIDGE_EXTRA_FEATURES[target]
    X = df_features[feature_columns]
    y = df_features[target]
    scaler, model = fit_ridge_full(X, y)

    # Test-set residual std + its historical relative-width median are the
    # basis for this target's prediction intervals and confidence threshold -
    # same methodology as forecast_model.py's test-period evaluation.
    y_test, _ridge_test_pred, residual_std = get_ridge_test_predictions(df_features, target)
    confidence_threshold = compute_confidence_threshold(y_test, residual_std)

    if target == "aluminium_price":
        forecast = forecast_aluminium(raw, scaler, model)
    else:
        forecast = forecast_pvc(raw, scaler, model)

    table = build_signal_table(
        forecast, raw[target], target, trailing_months, band_pct, residual_std, confidence_threshold
    )

    material = MATERIAL_LABELS[target]
    print(f"\n{'=' * 60}\n{material} procurement signal (next {FORECAST_HORIZON} months)\n{'=' * 60}")
    print(f"90% interval = forecast +/- {Z_90} * {residual_std:.2f} "
          f"(residual std from the test-period Ridge evaluation)")
    print(f"Confidence threshold: relative interval width <= {confidence_threshold:.1%} "
          f"of forecast price = High, above = Low "
          f"(threshold = historical median relative width over the test period)\n")
    print_forecast_ranges(table, target)
    print()
    print(table.drop(columns=["recommendation_detail"]).to_string(index=False))
    print_explanation(table, target, trailing_months)

    return table


def main(trailing_months: int = 6, band_pct: float = 0.03):
    """
    trailing_months: N in the trailing N-month average (default 6).
    band_pct: neutral band width as a fraction, e.g. 0.03 = +/-3% (default).
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df_features = load_features()
    df_features = add_aluminium_lag_features(df_features)
    raw = load_raw_prices()

    exposure_tables = []
    for target in TARGETS:
        table = run_for_target(df_features, raw, target, trailing_months, band_pct)

        out_path = os.path.join(OUTPUT_DIR, f"procurement_signal_{target}.csv")
        table.to_csv(out_path, index=False)
        print(f"\nSaved {out_path}")

        exposure_df = compute_cost_exposure(table, target, trailing_months)
        print(f"\nCost exposure ({RM_COST_SHARE_TOTAL:.0%} combined RM cost share, "
              f"{MATERIAL_COST_SHARE[target]:.0%} assumed for {MATERIAL_LABELS[target]}):")
        print_cost_exposure(exposure_df)
        exposure_tables.append(exposure_df)

    combined_exposure = pd.concat(exposure_tables, ignore_index=True)
    exposure_out_path = os.path.join(OUTPUT_DIR, "cost_exposure.csv")
    combined_exposure.to_csv(exposure_out_path, index=False)
    print(f"\nSaved {exposure_out_path}")


if __name__ == "__main__":
    main()
