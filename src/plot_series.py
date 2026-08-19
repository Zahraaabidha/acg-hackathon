"""
Plot the 5 monthly price/driver series from data/rm_price_data.csv.

Produces:
  plots/normalized_all_series.png   - all 5 series indexed to start=100
  plots/<column>.png                - one plot per raw series

Run with:
    python src/plot_series.py
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "rm_price_data.csv"
)
PLOTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plots")

COLUMNS = [
    "aluminium_price",
    "pvc_resin_price",
    "crude_oil_price",
    "usd_inr_rate",
    "freight_index",
]


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, index_col=0, parse_dates=True)
    df.index.name = "date"
    return df


def plot_normalized(df: pd.DataFrame) -> None:
    """All 5 series indexed to start=100 so differing scales are comparable."""
    normalized = df[COLUMNS] / df[COLUMNS].iloc[0] * 100

    fig, ax = plt.subplots(figsize=(12, 6))
    for column in COLUMNS:
        ax.plot(normalized.index, normalized[column], label=column)
    ax.axhline(100, color="gray", linewidth=0.8, linestyle="--")
    ax.set_title("All series normalized to start=100")
    ax.set_xlabel("Date")
    ax.set_ylabel("Index (start=100)")
    ax.legend()
    fig.tight_layout()

    out_path = os.path.join(PLOTS_DIR, "normalized_all_series.png")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Saved {out_path}")


def plot_individual(df: pd.DataFrame) -> None:
    """One plot per raw series, in its own units."""
    for column in COLUMNS:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(df.index, df[column], color="tab:blue")
        ax.set_title(column)
        ax.set_xlabel("Date")
        ax.set_ylabel(column)
        fig.tight_layout()

        out_path = os.path.join(PLOTS_DIR, f"{column}.png")
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        print(f"Saved {out_path}")


def _pct_change(df: pd.DataFrame, column: str, start: str, end: str):
    window = df.loc[start:end, column]
    if window.empty:
        return None
    return (window.iloc[-1] / window.iloc[0] - 1) * 100


def print_sanity_summary(df: pd.DataFrame) -> None:
    """
    Quantify the known real-world events over the same windows the plots cover,
    so a move that's visible on the chart but doesn't line up here (or vice versa)
    is a red flag for a bad join or misaligned date index, not just noise.
    """
    print("\nEvent sanity check (does the data reflect known real-world moves?):")

    covid_al = _pct_change(df, "aluminium_price", "2020-01-01", "2020-06-01")
    covid_pvc = _pct_change(df, "pvc_resin_price", "2020-01-01", "2020-06-01")
    print(
        f"  COVID dip (Jan-Jun 2020): aluminium {covid_al:+.1f}%, "
        f"PVC resin {covid_pvc:+.1f}% (expect a dip, roughly negative)"
    )

    supercycle_al = _pct_change(df, "aluminium_price", "2020-06-01", "2021-12-01")
    supercycle_pvc = _pct_change(df, "pvc_resin_price", "2020-06-01", "2021-12-01")
    print(
        f"  2021-2022 commodity supercycle (Jun 2020-Dec 2021): "
        f"aluminium {supercycle_al:+.1f}%, PVC resin {supercycle_pvc:+.1f}% "
        f"(expect a large positive move)"
    )

    energy_al = _pct_change(df, "aluminium_price", "2022-01-01", "2022-12-01")
    energy_pvc = _pct_change(df, "pvc_resin_price", "2022-01-01", "2022-12-01")
    print(
        f"  2022 energy crisis window (Jan-Dec 2022): aluminium {energy_al:+.1f}%, "
        f"PVC resin {energy_pvc:+.1f}% (aluminium smelting is energy-intensive, "
        f"expect volatility/elevated levels)"
    )

    print(
        "\n  Cross-check: inspect the saved PNGs to confirm these moves show up as "
        "a visible dip/surge on the chart in the right window. A real event with no "
        "matching plot movement, or a plot movement with no matching event above, "
        "points to a bad join or misaligned date index rather than genuine market data."
    )


def main():
    os.makedirs(PLOTS_DIR, exist_ok=True)
    df = load_data()

    plot_normalized(df)
    plot_individual(df)
    print_sanity_summary(df)


if __name__ == "__main__":
    main()
