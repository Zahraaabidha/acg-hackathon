"""
Compare a naive baseline, Ridge regression, and SARIMAX for forecasting
aluminium_price and pvc_resin_price, using the trimmed feature set from
data/rm_features.csv.

- Time-based split: last 12 months = test set, no shuffling.
- Ridge uses the lagged/rolling exogenous features only.
- SARIMAX uses the raw target series as endog plus the same trimmed
  exogenous features.
- Naive baseline: next month's price = this month's price (persistence).

Prints one MAE/RMSE/MAPE comparison table across all targets x models, Ridge
coefficients, SARIMAX order + AIC, and saves actual-vs-predicted plots.

Run with:
    python src/forecast_model.py
"""

import os
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeCV
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.statespace.sarimax import SARIMAX

warnings.filterwarnings("ignore")  # SARIMAX convergence/frequency warnings are expected here

FEATURES_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "rm_features.csv"
)
RAW_PRICES_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "rm_price_data.csv"
)
PLOTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plots")

TARGETS = ["aluminium_price", "pvc_resin_price"]
BASE_FEATURE_COLUMNS = [
    "crude_oil_price",
    "crude_oil_price_lag1",
    "crude_oil_price_roll3",
    "usd_inr_rate",
    "usd_inr_rate_lag6",
    "usd_inr_rate_roll3",
]

# Ridge has no built-in memory of its own, so aluminium_price gets explicit
# 1mo/3mo lags of itself as extra features (added after both models
# underperformed a naive persistence baseline without them). SARIMAX already
# has an autoregressive term via its (p,d,q) order, so its exog set is left
# unchanged for both targets to avoid feeding it a redundant/circular copy of
# the thing its AR term already models.
#
# energy_price_index (+ its 3mo rolling average) is also aluminium-only: it
# showed a 0.674 same-month correlation with aluminium_price in
# correlation_analysis.py (vs. 0.553 for pvc_resin_price, weaker than PVC's
# existing crude-oil features), matching the case study's listing of energy
# prices as an aluminium-specific driver (smelting is energy-intensive).
#
# shock_zscore_prior (feature_engineering.py's numeric shock/surge feature,
# reusing risk_alerts.py's anomaly z-score) is added to BOTH targets' Ridge
# models per the case study's "model inputs to include... price surge/shock
# events" requirement. It's added via RIDGE_EXTRA_FEATURES rather than
# BASE_FEATURE_COLUMNS specifically to keep SARIMAX's exog set unchanged,
# same reasoning as the self-lag/energy additions above.
RIDGE_EXTRA_FEATURES = {
    "aluminium_price": [
        "aluminium_price_lag1",
        "aluminium_price_lag3",
        "energy_price_index",
        "energy_price_index_roll3",
        "shock_zscore_prior",
    ],
    "pvc_resin_price": ["shock_zscore_prior"],
}

TEST_SIZE = 12
SARIMAX_ORDER = (1, 1, 1)
SARIMAX_SEASONAL_ORDER = (0, 0, 0, 0)

# z-score for an approximate 90% prediction interval, assuming ~normal
# residuals - a simple, defensible choice given the small sample size
# (not worth bootstrapping ~84 training rows).
Z_90 = 1.645


def load_data() -> pd.DataFrame:
    df = pd.read_csv(FEATURES_PATH, index_col=0, parse_dates=True)
    df.index.name = "date"
    return df


def add_aluminium_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Attach aluminium_price_lag1/lag3, computed from the full raw price
    history (not the already-trimmed feature file), so no rows are lost to
    NaNs that wouldn't exist if we'd shifted within the trimmed date range.
    """
    raw_aluminium = pd.read_csv(RAW_PRICES_PATH, index_col=0, parse_dates=True)[
        "aluminium_price"
    ]
    df = df.copy()
    df["aluminium_price_lag1"] = raw_aluminium.shift(1).reindex(df.index)
    df["aluminium_price_lag3"] = raw_aluminium.shift(3).reindex(df.index)
    return df


def time_split(df: pd.DataFrame, test_size: int) -> tuple:
    return df.iloc[:-test_size], df.iloc[-test_size:]


def compute_metrics(y_true: pd.Series, y_pred: np.ndarray) -> dict:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mae = np.mean(np.abs(y_true - y_pred))
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    return {"MAE": mae, "RMSE": rmse, "MAPE": mape}


def compute_directional_accuracy(y_true, y_pred, y_prev) -> float:
    """
    % of test months where the model correctly called the DIRECTION of price
    movement (up/down vs. the actual previous month), not just the magnitude.

    y_prev is the actual price one month before each test point (known,
    real information - not a model output), so this is a fair comparison
    across naive/Ridge/SARIMAX. Note the naive baseline predicts "no change"
    every month by construction, so its predicted direction is always flat -
    it can never be credited with correctly calling an up or down move,
    which is an expected mathematical property of a persistence model, not
    a bug in this metric.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    y_prev = np.asarray(y_prev, dtype=float)

    actual_direction = np.sign(y_true - y_prev)
    predicted_direction = np.sign(y_pred - y_prev)
    return float(np.mean(actual_direction == predicted_direction)) * 100


def compute_residual_std(y_true, y_pred) -> float:
    """Std dev of (actual - predicted) - the basis for the +/-Z_90*std interval."""
    residuals = np.asarray(y_true, dtype=float) - np.asarray(y_pred, dtype=float)
    return float(np.std(residuals, ddof=1))


def get_ridge_test_predictions(df: pd.DataFrame, target: str) -> tuple:
    """
    Refit Ridge on the same train/test split used in run_for_target() and
    return (y_test, y_pred, residual_std). Exposed standalone so
    procurement_signal.py can build prediction intervals and a confidence
    threshold for its 3-month-ahead forecasts using the exact same
    methodology as the test-period evaluation here, without duplicating the
    fitting logic.
    """
    feature_columns = BASE_FEATURE_COLUMNS + RIDGE_EXTRA_FEATURES[target]
    X = df[feature_columns]
    y = df[target]

    X_train, X_test = time_split(X, TEST_SIZE)
    y_train, y_test = time_split(y, TEST_SIZE)

    y_pred, _coefficients, _alpha = fit_ridge(X_train, y_train, X_test)
    residual_std = compute_residual_std(y_test.values, y_pred)
    return y_test, y_pred, residual_std


def fit_naive_baseline(full_series: pd.Series, test_index: pd.DatetimeIndex) -> np.ndarray:
    """Persistence model: forecast for month t is the actual value at t-1."""
    shifted = full_series.shift(1)
    return shifted.loc[test_index].values


def fit_ridge(X_train, y_train, X_test) -> tuple:
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = RidgeCV(alphas=[0.1, 1.0, 10.0, 100.0])
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)
    coefficients = pd.Series(model.coef_, index=X_train.columns).sort_values(
        key=abs, ascending=False
    )
    return y_pred, coefficients, model.alpha_


def fit_sarimax(y_train, X_train, y_test, X_test) -> tuple:
    model = SARIMAX(
        y_train,
        exog=X_train,
        order=SARIMAX_ORDER,
        seasonal_order=SARIMAX_SEASONAL_ORDER,
        enforce_stationarity=False,
        enforce_invertibility=False,
    )
    fitted = model.fit(disp=False)

    forecast = fitted.get_forecast(steps=len(y_test), exog=X_test)
    y_pred = forecast.predicted_mean.values
    return y_pred, fitted.aic, fitted


def plot_actual_vs_predicted(
    test_index, y_test, ridge_pred, sarimax_pred, ridge_lower, ridge_upper, target: str
) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.fill_between(
        test_index, ridge_lower, ridge_upper, color="tab:blue", alpha=0.15,
        label="Ridge 90% interval",
    )
    ax.plot(test_index, y_test, label="actual", color="black", marker="o")
    ax.plot(test_index, ridge_pred, label="Ridge", color="tab:blue", marker="o")
    ax.plot(test_index, sarimax_pred, label="SARIMAX", color="tab:orange", marker="o")
    ax.set_title(f"{target}: actual vs predicted (test period)")
    ax.set_xlabel("Date")
    ax.set_ylabel(target)
    ax.legend()
    fig.tight_layout()

    out_path = os.path.join(PLOTS_DIR, f"forecast_{target}.png")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Saved {out_path}")


def run_for_target(df: pd.DataFrame, target: str) -> dict:
    ridge_feature_columns = BASE_FEATURE_COLUMNS + RIDGE_EXTRA_FEATURES[target]
    sarimax_feature_columns = BASE_FEATURE_COLUMNS

    y = df[target]
    X_ridge = df[ridge_feature_columns]
    X_sarimax = df[sarimax_feature_columns]

    X_ridge_train, X_ridge_test = time_split(X_ridge, TEST_SIZE)
    X_sarimax_train, X_sarimax_test = time_split(X_sarimax, TEST_SIZE)
    y_train, y_test = time_split(y, TEST_SIZE)

    naive_pred = fit_naive_baseline(y, y_test.index)
    ridge_pred, ridge_coefficients, ridge_alpha = fit_ridge(X_ridge_train, y_train, X_ridge_test)
    sarimax_pred, sarimax_aic, sarimax_fitted = fit_sarimax(
        y_train, X_sarimax_train, y_test, X_sarimax_test
    )

    ridge_residual_std = compute_residual_std(y_test.values, ridge_pred)
    ridge_lower = ridge_pred - Z_90 * ridge_residual_std
    ridge_upper = ridge_pred + Z_90 * ridge_residual_std

    # Actual price one month before each test point - real, known information,
    # used as the common "did we call the direction right?" reference for all
    # three approaches.
    y_prev = y.shift(1).loc[y_test.index].values

    metrics = {
        "naive": {
            **compute_metrics(y_test, naive_pred),
            "Directional Accuracy": compute_directional_accuracy(y_test, naive_pred, y_prev),
        },
        "ridge": {
            **compute_metrics(y_test, ridge_pred),
            "Directional Accuracy": compute_directional_accuracy(y_test, ridge_pred, y_prev),
        },
        "sarimax": {
            **compute_metrics(y_test, sarimax_pred),
            "Directional Accuracy": compute_directional_accuracy(y_test, sarimax_pred, y_prev),
        },
    }

    print(f"\n{'=' * 60}\nTarget: {target}\n{'=' * 60}")

    print(f"\nRidge (alpha={ridge_alpha:g}) standardized coefficients:")
    for name, coef in ridge_coefficients.items():
        print(f"  {name:<24} {coef:+.3f}")

    print(f"\nSARIMAX order: {SARIMAX_ORDER}{SARIMAX_SEASONAL_ORDER} | AIC: {sarimax_aic:.2f}")
    resid = sarimax_fitted.resid
    print(f"SARIMAX residuals (train): mean={resid.mean():.3f}, std={resid.std():.3f}")

    print(f"\nRidge test-set residual std: {ridge_residual_std:.2f} "
          f"(90% interval = forecast +/- {Z_90} * {ridge_residual_std:.2f})")

    plot_actual_vs_predicted(
        y_test.index, y_test.values, ridge_pred, sarimax_pred, ridge_lower, ridge_upper, target
    )

    ridge_rmse = metrics["ridge"]["RMSE"]
    sarimax_rmse = metrics["sarimax"]["RMSE"]
    if ridge_rmse < sarimax_rmse:
        pct = (sarimax_rmse - ridge_rmse) / sarimax_rmse * 100
        print(f"\nVerdict: Ridge wins for {target} (RMSE {ridge_rmse:.2f} vs {sarimax_rmse:.2f}, "
              f"{pct:.1f}% lower error)")
    else:
        pct = (ridge_rmse - sarimax_rmse) / ridge_rmse * 100
        print(f"\nVerdict: SARIMAX wins for {target} (RMSE {sarimax_rmse:.2f} vs {ridge_rmse:.2f}, "
              f"{pct:.1f}% lower error)")

    return metrics


def print_comparison_table(all_metrics: dict) -> None:
    rows = []
    for target, model_metrics in all_metrics.items():
        for model_name, metrics in model_metrics.items():
            rows.append(
                {
                    "target": target,
                    "model": model_name,
                    "MAE": metrics["MAE"],
                    "RMSE": metrics["RMSE"],
                    "MAPE (%)": metrics["MAPE"],
                    "Directional Accuracy (%)": metrics["Directional Accuracy"],
                }
            )
    table = pd.DataFrame(rows).set_index(["target", "model"]).round(3)
    print(f"\n{'=' * 60}\nComparison table (test set, last {TEST_SIZE} months)\n{'=' * 60}")
    print(table.to_string())


def main():
    os.makedirs(PLOTS_DIR, exist_ok=True)
    df = load_data()
    df = add_aluminium_lag_features(df)

    all_metrics = {}
    for target in TARGETS:
        all_metrics[target] = run_for_target(df, target)

    print_comparison_table(all_metrics)


if __name__ == "__main__":
    main()
