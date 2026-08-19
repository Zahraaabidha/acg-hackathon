"""
Correlation analysis for data/rm_price_data.csv.

- Full 5x5 Pearson correlation matrix (printed + heatmap PNG).
- Lagged correlation of each external predictor (crude_oil_price, usd_inr_rate,
  freight_index) against each target (aluminium_price, pvc_resin_price) at
  lags of 0 (same month), 1, 2, 3, 6 months.
- Ranked list of the strongest (predictor, lag) pairs per target.

Predictors are scoped to the 3 external drivers (not the targets themselves),
matching the causal knowledge graph: aluminium_price/pvc_resin_price are the
outcomes, crude_oil_price/usd_inr_rate/freight_index are upstream drivers.

Run with:
    python src/correlation_analysis.py
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "rm_price_data.csv"
)
PLOTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plots")

ALL_COLUMNS = [
    "aluminium_price",
    "pvc_resin_price",
    "crude_oil_price",
    "usd_inr_rate",
    "freight_index",
    "energy_price_index",
    "demand_index",
]
TARGETS = ["aluminium_price", "pvc_resin_price"]
PREDICTORS = ["crude_oil_price", "usd_inr_rate", "freight_index", "energy_price_index", "demand_index"]
LAGS = [0, 1, 2, 3, 6]


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, index_col=0, parse_dates=True)
    df.index.name = "date"
    return df


def print_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    corr = df[ALL_COLUMNS].corr(method="pearson")
    print("Full pairwise Pearson correlation matrix:\n")
    print(corr.round(3).to_string())
    return corr


def plot_correlation_heatmap(corr: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(corr.values, vmin=-1, vmax=1, cmap="RdBu_r")

    ax.set_xticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(corr.index)))
    ax.set_yticklabels(corr.index)

    for i in range(len(corr.index)):
        for j in range(len(corr.columns)):
            ax.text(
                j, i, f"{corr.values[i, j]:.2f}",
                ha="center", va="center",
                color="white" if abs(corr.values[i, j]) > 0.6 else "black",
                fontsize=9,
            )

    ax.set_title("Pearson correlation matrix")
    fig.colorbar(im, ax=ax, shrink=0.8, label="correlation")
    fig.tight_layout()

    out_path = os.path.join(PLOTS_DIR, "correlation_heatmap.png")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"\nSaved {out_path}")


def compute_lagged_correlations(df: pd.DataFrame) -> pd.DataFrame:
    """
    corr(target[t], predictor[t - lag]) for each predictor/target/lag combo.
    lag=0 is the same-month correlation already shown in the full matrix.
    """
    rows = []
    for target in TARGETS:
        for predictor in PREDICTORS:
            for lag in LAGS:
                shifted = df[predictor].shift(lag)
                corr = df[target].corr(shifted)
                rows.append(
                    {
                        "target": target,
                        "predictor": predictor,
                        "lag_months": lag,
                        "correlation": corr,
                    }
                )
    return pd.DataFrame(rows)


def print_lagged_correlations(lag_df: pd.DataFrame) -> None:
    print("\nLagged correlations (predictor at t-lag vs target at t):\n")
    for target in TARGETS:
        subset = lag_df[lag_df["target"] == target].copy()
        pivot = subset.pivot(index="predictor", columns="lag_months", values="correlation")
        pivot = pivot[LAGS]  # keep column order
        print(f"  {target}:")
        print(pivot.round(3).to_string(), "\n")


def print_ranked_pairs(lag_df: pd.DataFrame) -> None:
    print("Ranked (predictor, lag) pairs by |correlation| with each target:\n")
    for target in TARGETS:
        subset = lag_df[lag_df["target"] == target].copy()
        subset["abs_correlation"] = subset["correlation"].abs()
        subset = subset.sort_values("abs_correlation", ascending=False)

        print(f"  {target}:")
        for _, row in subset.iterrows():
            lag_label = "same-month" if row["lag_months"] == 0 else f"lag {int(row['lag_months'])}mo"
            print(
                f"    {row['predictor']:<18} {lag_label:<12} "
                f"corr = {row['correlation']:+.3f}"
            )
        print()


def main():
    os.makedirs(PLOTS_DIR, exist_ok=True)
    df = load_data()

    corr = print_correlation_matrix(df)
    plot_correlation_heatmap(corr)

    lag_df = compute_lagged_correlations(df)
    print_lagged_correlations(lag_df)
    print_ranked_pairs(lag_df)


if __name__ == "__main__":
    main()
