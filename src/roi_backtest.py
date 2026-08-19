"""
ROI backtest: walk forward across the full available history and ask "what
would ACG have spent under the model-guided buy/wait signal vs buying
reactively every month?" - covering periods with real price down-swings
(e.g. the 2022 correction), not just the recent uptrend-dominated year.

WALK-FORWARD METHOD (no lookahead):
  - Start with an initial training window of the first WALKFORWARD_INITIAL_MONTHS
    months.
  - For each subsequent month, refit Ridge using only data available up to
    that point, forecast that one month, generate its buy/wait/neutral
    signal, then move forward one month and repeat.
  - The model never sees a given month's actual price - or any later month's
    data - when generating that month's signal.

Two strategies, same total volume, only the TIMING of purchases differs:
  1. NAIVE/REACTIVE - buy a fixed monthly quantity at that month's actual
     price, no timing.
  2. MODEL-GUIDED - defer "Wait" months' purchases to the next Buy-now/Neutral
     month, capped at a max deferral window. Total volume purchased matches
     the naive strategy exactly - only which month it's bought in changes.

Saves output/roi_backtest.csv (overall) and output/roi_backtest_by_year.csv,
and prints an explicitly-caveated summary - see print_assumptions() for
exactly what's simplified. If the result is small even over this longer,
more volatile window, that's reported as-is, not adjusted to look bigger.

Run with:
    python src/roi_backtest.py
"""

import os
import sys

import pandas as pd
from sklearn.linear_model import RidgeCV
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(__file__))
from forecast_model import (  # noqa: E402
    BASE_FEATURE_COLUMNS,
    RIDGE_EXTRA_FEATURES,
    add_aluminium_lag_features,
)
from procurement_signal import MATERIAL_LABELS, classify_recommendation  # noqa: E402

RAW_PRICES_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "rm_price_data.csv"
)
FEATURES_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "rm_features.csv"
)
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")

TARGETS = ["aluminium_price", "pvc_resin_price"]

# --- Simulation parameters (tune these, not the logic, if numbers need to change) ---
WALKFORWARD_INITIAL_MONTHS = 24  # months of initial training history before the first signal
MONTHLY_VOLUME = 100  # placeholder tonnes/month - real client volume not provided
TRAILING_MONTHS = 6
NEUTRAL_BAND_PCT = 0.03
MAX_DEFER_MONTHS = 2


def load_raw_prices() -> pd.DataFrame:
    df = pd.read_csv(RAW_PRICES_PATH, index_col=0, parse_dates=True)
    df.index.name = "date"
    return df


def load_features() -> pd.DataFrame:
    df = pd.read_csv(FEATURES_PATH, index_col=0, parse_dates=True)
    df.index.name = "date"
    return df


def get_walkforward_predictions(
    df_features: pd.DataFrame, target: str, initial_train_months: int
) -> pd.Series:
    """
    Expanding-window walk-forward: refit Ridge fresh at every step using only
    data strictly before the forecasted month, so no future information ever
    leaks into a given month's forecast.
    """
    feature_columns = BASE_FEATURE_COLUMNS + RIDGE_EXTRA_FEATURES[target]
    X = df_features[feature_columns]
    y = df_features[target]

    predictions = {}
    for i in range(initial_train_months, len(df_features)):
        X_train, y_train = X.iloc[:i], y.iloc[:i]
        X_step = X.iloc[[i]]

        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_step_scaled = scaler.transform(X_step)

        model = RidgeCV(alphas=[0.1, 1.0, 10.0, 100.0])
        model.fit(X_train_scaled, y_train)

        date = df_features.index[i]
        predictions[date] = model.predict(X_step_scaled)[0]

    return pd.Series(predictions)


def compute_trailing_avg(raw_series: pd.Series, as_of_date, trailing_months: int) -> float:
    """Trailing average using only actual prices known strictly before as_of_date."""
    history = raw_series.loc[:as_of_date].iloc[:-1]
    return history.iloc[-trailing_months:].mean()


def build_monthly_signals(
    pred_series: pd.Series, raw_series: pd.Series, trailing_months: int, band_pct: float
) -> tuple:
    signals, trailing_avgs = {}, {}
    for date, forecast_price in pred_series.items():
        trailing_avg = compute_trailing_avg(raw_series, date, trailing_months)
        trailing_avgs[date] = trailing_avg
        signals[date] = classify_recommendation(forecast_price, trailing_avg, band_pct)
    return signals, trailing_avgs


def simulate_model_guided(
    actual_prices: pd.Series, signals: dict, monthly_volume: float, max_defer: int
) -> dict:
    """
    Walk the months in order. A month flagged "Wait" pushes its purchase
    forward to the first upcoming month (within max_defer months) flagged
    "Buy now" or "Neutral / Monitor". If nothing qualifies within the window,
    force the buy at the deferral cap anyway - a real team can't wait forever
    and total volume must still match the naive strategy. Purchases from
    different origin months can land in the same target month.

    Returns {month: quantity actually bought that month}.
    """
    months = list(actual_prices.index)
    n = len(months)
    purchases = {m: 0.0 for m in months}

    for i, month in enumerate(months):
        if signals[month] != "Wait":
            buy_index = i
        else:
            buy_index = None
            for offset in range(1, max_defer + 1):
                j = i + offset
                if j >= n:
                    break
                if signals[months[j]] != "Wait":
                    buy_index = j
                    break
            if buy_index is None:
                buy_index = min(i + max_defer, n - 1)  # forced buy at the deferral cap

        purchases[months[buy_index]] += monthly_volume

    return purchases


def run_for_target(
    df_features: pd.DataFrame,
    raw: pd.DataFrame,
    target: str,
    initial_train_months: int,
    trailing_months: int,
    band_pct: float,
    monthly_volume: float,
    max_defer: int,
) -> dict:
    pred_series = get_walkforward_predictions(df_features, target, initial_train_months)
    actual_prices = raw[target].loc[pred_series.index]

    signals, trailing_avgs = build_monthly_signals(
        pred_series, raw[target], trailing_months, band_pct
    )
    purchases = simulate_model_guided(actual_prices, signals, monthly_volume, max_defer)

    naive_spend_by_month = actual_prices * monthly_volume
    model_spend_by_month = pd.Series(purchases) * actual_prices

    return {
        "naive_spend_by_month": naive_spend_by_month,
        "model_spend_by_month": model_spend_by_month,
        "signals": signals,
    }


def summarize(naive_spend_by_month: pd.Series, model_spend_by_month: pd.Series) -> dict:
    naive_spend = float(naive_spend_by_month.sum())
    model_spend = float(model_spend_by_month.sum())
    savings = naive_spend - model_spend
    savings_pct = savings / naive_spend * 100
    return {
        "naive_spend": naive_spend,
        "model_spend": model_spend,
        "savings": savings,
        "savings_pct": savings_pct,
    }


def yearly_breakdown(naive_spend_by_month: pd.Series, model_spend_by_month: pd.Series) -> pd.DataFrame:
    naive_by_year = naive_spend_by_month.groupby(naive_spend_by_month.index.year).sum()
    model_by_year = model_spend_by_month.groupby(model_spend_by_month.index.year).sum()

    rows = []
    for year in naive_by_year.index:
        naive = naive_by_year[year]
        model = model_by_year.get(year, naive)
        savings = naive - model
        rows.append(
            {
                "year": year,
                "naive_spend": round(naive, 2),
                "model_guided_spend": round(model, 2),
                "savings": round(savings, 2),
                "savings_pct": round(savings / naive * 100, 2),
            }
        )
    return pd.DataFrame(rows)


def print_assumptions() -> None:
    print("Simplifying assumptions in this backtest (illustrative, not audited figures):")
    print(
        f"  - Walk-forward, no lookahead: Ridge is refit at every step using only data before "
        f"the forecasted month (expanding window, starting from {WALKFORWARD_INITIAL_MONTHS} "
        f"months of initial training history). A month's signal never sees that month's own "
        f"actual price, or any later month's data."
    )
    print(
        f"  - Fixed purchase volume of {MONTHLY_VOLUME} tonnes/month, same for both materials "
        f"- real client volume data wasn't provided. Dollar totals scale with this number; "
        f"the %% savings figure does NOT, since both strategies buy the same total volume."
    )
    print(
        f"  - A 'Wait' month can be deferred at most {MAX_DEFER_MONTHS} months before being "
        f"forced through regardless of signal - a procurement team can't wait forever."
    )
    print("  - No storage, carrying, or financing cost is modeled for deferred purchases.")
    print("  - No minimum-order-quantity or supplier contract constraints are modeled.")
    print(
        "  - pvc_resin_price is a PPI-index proxy, not a literal $/tonne market price, so "
        "the combined total below treats both materials' price units as comparable purely "
        "for illustration."
    )


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df_features = load_features()
    df_features = add_aluminium_lag_features(df_features)
    raw = load_raw_prices()

    print_assumptions()

    results = {}
    for target in TARGETS:
        results[target] = run_for_target(
            df_features,
            raw,
            target,
            WALKFORWARD_INITIAL_MONTHS,
            TRAILING_MONTHS,
            NEUTRAL_BAND_PCT,
            MONTHLY_VOLUME,
            MAX_DEFER_MONTHS,
        )

    window_start = list(results.values())[0]["naive_spend_by_month"].index.min()
    window_end = list(results.values())[0]["naive_spend_by_month"].index.max()
    n_months = len(list(results.values())[0]["naive_spend_by_month"])
    print(
        f"\nWalk-forward window: {window_start.strftime('%Y-%m')} to "
        f"{window_end.strftime('%Y-%m')} ({n_months} months)"
    )

    combined_naive_by_month = None
    combined_model_by_month = None

    for target in TARGETS:
        material = MATERIAL_LABELS[target]
        r = results[target]
        summary = summarize(r["naive_spend_by_month"], r["model_spend_by_month"])
        year_table = yearly_breakdown(r["naive_spend_by_month"], r["model_spend_by_month"])

        print(f"\n{'=' * 70}\n{material} ROI backtest (walk-forward, {n_months} months)\n{'=' * 70}")
        print(f"Naive/reactive total spend: {summary['naive_spend']:,.2f}")
        print(f"Model-guided total spend:   {summary['model_spend']:,.2f}")
        print(f"Savings: {summary['savings']:,.2f} ({summary['savings_pct']:.2f}%)")
        print(f"\nSavings by year:")
        print(year_table.to_string(index=False))

        year_table.insert(0, "material", material)
        year_table.to_csv(
            os.path.join(OUTPUT_DIR, f"roi_backtest_by_year_{target}.csv"), index=False
        )

        if combined_naive_by_month is None:
            combined_naive_by_month = r["naive_spend_by_month"].copy()
            combined_model_by_month = r["model_spend_by_month"].copy()
        else:
            combined_naive_by_month = combined_naive_by_month.add(r["naive_spend_by_month"], fill_value=0)
            combined_model_by_month = combined_model_by_month.add(r["model_spend_by_month"], fill_value=0)

    combined_summary = summarize(combined_naive_by_month, combined_model_by_month)
    combined_year_table = yearly_breakdown(combined_naive_by_month, combined_model_by_month)

    print(f"\n{'=' * 70}\nCombined (aluminium + PVC resin, illustrative)\n{'=' * 70}")
    print(f"Naive/reactive total spend: {combined_summary['naive_spend']:,.2f}")
    print(f"Model-guided total spend:   {combined_summary['model_spend']:,.2f}")
    print(f"Savings: {combined_summary['savings']:,.2f} ({combined_summary['savings_pct']:.2f}%)")
    print(f"\nCombined savings by year:")
    print(combined_year_table.to_string(index=False))

    if abs(combined_summary["savings_pct"]) < 1.0:
        print(
            f"\nNote: combined savings are small ({combined_summary['savings_pct']:.2f}%) even "
            f"over this longer, more volatile window - reporting this as-is rather than adjusting "
            f"the simulation to produce a bigger number."
        )

    summary_rows = []
    for target in TARGETS:
        r = results[target]
        s = summarize(r["naive_spend_by_month"], r["model_spend_by_month"])
        summary_rows.append(
            {
                "material": MATERIAL_LABELS[target],
                "naive_spend": round(s["naive_spend"], 2),
                "model_guided_spend": round(s["model_spend"], 2),
                "savings": round(s["savings"], 2),
                "savings_pct": round(s["savings_pct"], 2),
            }
        )
    summary_rows.append(
        {
            "material": "Combined",
            "naive_spend": round(combined_summary["naive_spend"], 2),
            "model_guided_spend": round(combined_summary["model_spend"], 2),
            "savings": round(combined_summary["savings"], 2),
            "savings_pct": round(combined_summary["savings_pct"], 2),
        }
    )
    summary_df = pd.DataFrame(summary_rows)
    out_path = os.path.join(OUTPUT_DIR, "roi_backtest.csv")
    summary_df.to_csv(out_path, index=False)
    print(f"\nSaved {out_path}")

    combined_year_table.insert(0, "material", "Combined")
    combined_year_table.to_csv(os.path.join(OUTPUT_DIR, "roi_backtest_by_year.csv"), index=False)
    print(f"Saved {os.path.join(OUTPUT_DIR, 'roi_backtest_by_year.csv')}")

    print(
        f"\nModel-guided timing would have saved ~{combined_summary['savings_pct']:.1f}% on RM "
        f"spend over the {n_months}-month walk-forward backtest "
        f"({window_start.strftime('%Y-%m')} to {window_end.strftime('%Y-%m')})."
    )


if __name__ == "__main__":
    main()
