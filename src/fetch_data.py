"""
Fetch raw-material price and driver data from FRED and Yahoo Finance,
align everything to monthly frequency, and save to data/rm_price_data.csv.

Series pulled:
  FRED  PALUMUSDM        -> aluminium_price
  FRED  PCU325211325211  -> pvc_resin_price   (PPI proxy)
  FRED  DCOILWTICO       -> crude_oil_price
  FRED  DEXINUS          -> usd_inr_rate
  FRED  PCU221122221122  -> energy_price_index (US electric power PPI - aluminium smelting is
                                                 energy-intensive, per the case study's driver list)
  FRED  INDPRO           -> demand_index      (US Industrial Production: Total Index - demand-side
                                                proxy for both aluminium and PVC end-use industries)
  yfinance BDRY          -> freight_index     (Baltic Dry Index proxy)

Requires the FRED_API_KEY environment variable (free key at
https://fred.stlouisfed.org/docs/api/api_key.html). The key is never
hardcoded or written to disk.

Run with:
    python src/fetch_data.py
"""

import os

import pandas as pd
import yfinance as yf
from dotenv import load_dotenv
from fredapi import Fred

load_dotenv()  # loads FRED_API_KEY from a local .env file, if present

FRED_SERIES = {
    "PALUMUSDM": "aluminium_price",
    "PCU325211325211": "pvc_resin_price",
    "DCOILWTICO": "crude_oil_price",
    "DEXINUS": "usd_inr_rate",
    # "Producer Price Index by Industry: Electric Power Distribution" - free,
    # public BLS series via FRED, monthly, back to Dec 2003 (well before our
    # 2018-03 start). Verified at https://fred.stlouisfed.org/series/PCU221122221122
    "PCU221122221122": "energy_price_index",
    # "Industrial Production: Total Index" - free, public Federal Reserve
    # Board series via FRED, monthly, seasonally adjusted, back to 1919.
    # Verified at https://fred.stlouisfed.org/series/INDPRO
    "INDPRO": "demand_index",
}
YF_TICKER = "BDRY"
YF_COLUMN_NAME = "freight_index"
YF_START_DATE = "2018-01-01"  # BDRY's actual listing date; yfinance defaults to a
                               # ~1 month lookback if start/period aren't given

OUTPUT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "rm_price_data.csv"
)


def fetch_fred_series() -> pd.DataFrame:
    """Pull each FRED series and resample to monthly-start mean."""
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        raise RuntimeError(
            "FRED_API_KEY environment variable is not set. "
            "Get a free key at https://fred.stlouisfed.org/docs/api/api_key.html"
        )
    fred = Fred(api_key=api_key)

    columns = {}
    for series_id, column_name in FRED_SERIES.items():
        series = fred.get_series(series_id)
        series.index = pd.to_datetime(series.index)
        # Resampling an already-monthly series to monthly mean is a no-op;
        # this uniformly handles both daily (DCOILWTICO, DEXINUS) and
        # monthly (PALUMUSDM, PCU325211325211) source frequencies.
        columns[column_name] = series.resample("MS").mean()

    return pd.DataFrame(columns)


def fetch_freight_index() -> pd.Series:
    """Pull BDRY daily closes and resample to monthly mean as a freight-rate proxy."""
    data = yf.download(
        YF_TICKER, start=YF_START_DATE, end=None, progress=False, auto_adjust=True
    )
    if data.empty:
        raise RuntimeError(f"yfinance returned no data for ticker {YF_TICKER!r}")

    close = data["Close"]
    if isinstance(close, pd.DataFrame):  # yfinance can return a MultiIndex column
        close = close.iloc[:, 0]
    close.index = pd.to_datetime(close.index)

    monthly = close.resample("MS").mean()
    monthly.name = YF_COLUMN_NAME
    return monthly


def truncate_to_common_start(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop leading rows before every column has started reporting data.

    Forward-fill can't repair leading NaNs (there's nothing earlier to carry
    forward), so a column with a late start date - like BDRY, which only goes
    back to ~2018 - leaves the whole dataset mostly-missing for that column
    unless we first truncate to the latest of all per-column start dates.
    """
    first_valid_dates = df.apply(lambda col: col.first_valid_index())
    common_start = first_valid_dates.max()

    rows_before = len(df)
    truncated = df.loc[common_start:]
    rows_dropped = rows_before - len(truncated)

    print(f"\nPer-column first valid date:")
    for column, date in first_valid_dates.items():
        print(f"  {column}: {date.date()}")
    print(f"Common start date (latest of the above): {common_start.date()}")
    print(f"Rows dropped by truncation: {rows_dropped} (of {rows_before})")

    return truncated


def build_dataset() -> pd.DataFrame:
    """Merge all series, truncate to a common start date, then forward-fill gaps."""
    fred_df = fetch_fred_series()
    freight = fetch_freight_index()

    merged = fred_df.join(freight, how="outer").sort_index()
    merged = truncate_to_common_start(merged)
    merged = merged.ffill()
    return merged


def print_summary(df: pd.DataFrame) -> None:
    print(f"\nDate range: {df.index.min().date()} to {df.index.max().date()}")
    print(f"Rows: {len(df)}")

    print("\nMissing values after forward-fill (%):")
    missing_pct = (df.isna().mean() * 100).round(2)
    for column, pct in missing_pct.items():
        print(f"  {column}: {pct}%")

    print("\nCorrelation of freight_index with price targets:")
    for target in ["aluminium_price", "pvc_resin_price"]:
        corr = df["freight_index"].corr(df[target])
        print(f"  freight_index vs {target}: {corr:.3f}")


def main():
    df = build_dataset()

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH)
    print(f"Saved {len(df)} rows to {OUTPUT_PATH}")

    print_summary(df)


if __name__ == "__main__":
    main()
