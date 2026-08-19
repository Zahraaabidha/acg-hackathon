"""
Minimal Streamlit dashboard for the raw material price forecasting pipeline.

Reads ONLY from saved files in /data and /output - no live API calls, no live
model refitting - so it's safe to demo on camera without any network risk.
Regenerate the underlying files first with the pipeline scripts (fetch_data.py
-> correlation_analysis.py -> feature_engineering.py -> forecast_model.py ->
procurement_signal.py -> risk_alerts.py -> narrative_generator.py -> main.py)
whenever you want the dashboard to reflect fresh numbers.

Run with:
    streamlit run src/dashboard.py
"""

import os
from datetime import date

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")

# Kept in sync with procurement_signal.py's MATERIAL_LABELS by hand, rather
# than importing that module - the dashboard has no dependency on the
# modeling code (sklearn/statsmodels/fredapi), just pandas/matplotlib, so a
# broken pipeline environment can't take the demo down with it.
MATERIALS = {
    "aluminium_price": "Aluminium",
    "pvc_resin_price": "PVC resin",
}

st.set_page_config(page_title="RM Price Forecast Dashboard", layout="wide")


# --- Safe loaders -----------------------------------------------------------
# Every file read returns None on any failure (missing file, bad CSV, etc.)
# instead of raising, so the page always renders something legible - a
# fallback message per section, never a stack trace on camera.

def load_raw_prices():
    try:
        df = pd.read_csv(
            os.path.join(DATA_DIR, "rm_price_data.csv"), index_col=0, parse_dates=True
        )
        return df
    except Exception:
        return None


def load_signal_table(target: str):
    try:
        return pd.read_csv(os.path.join(OUTPUT_DIR, f"procurement_signal_{target}.csv"))
    except Exception:
        return None


def load_narratives():
    try:
        with open(os.path.join(OUTPUT_DIR, "forecast_narratives.txt"), "r", encoding="utf-8") as f:
            text = f.read()
        return [p.strip() for p in text.split("\n\n") if p.strip()]
    except Exception:
        return None


def load_risk_alerts():
    try:
        return pd.read_csv(os.path.join(OUTPUT_DIR, "risk_alerts.csv"))
    except Exception:
        return None


def load_graph_html():
    try:
        with open(os.path.join(OUTPUT_DIR, "price_driver_graph.html"), "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


# --- Chart --------------------------------------------------------------

def plot_forecast_chart(raw_df, signal_df, target: str, label: str):
    """Recent actual price + the 6-month Ridge forecast with its 90% interval
    band, styled to match forecast_model.py's saved plots (black actual line,
    blue forecast line + shaded band). Built from the saved CSVs only - no
    model is refit here."""
    fig, ax = plt.subplots(figsize=(8, 4))

    if raw_df is not None and target in raw_df.columns:
        history = raw_df[target].iloc[-12:]
        ax.plot(history.index, history.values, label="actual", color="black", marker="o", markersize=3)

    if signal_df is not None:
        dates = pd.to_datetime(signal_df["month"])
        ax.fill_between(
            dates, signal_df["interval_low"], signal_df["interval_high"],
            color="tab:blue", alpha=0.15, label="90% interval",
        )
        ax.plot(dates, signal_df["forecasted_price"], label="Ridge forecast", color="tab:blue", marker="o")

    ax.set_title(f"{label}: 6-month forecast")
    ax.set_xlabel("Date")
    ax.set_ylabel(label)
    ax.legend()
    fig.tight_layout()
    return fig


def find_narrative(narratives: list, label: str, month: str):
    if not narratives:
        return None
    for paragraph in narratives:
        if paragraph.startswith(label) and f"for {month}." in paragraph:
            return paragraph
    return None


# --- Page ---------------------------------------------------------------

def render_header(raw_df):
    st.title("Raw Material Price Forecast Dashboard")
    materials_text = " & ".join(MATERIALS.values())
    caption = f"{materials_text} - viewed {date.today().strftime('%Y-%m-%d')}"
    if raw_df is not None and not raw_df.empty:
        caption += f" - data as of {raw_df.index.max().strftime('%Y-%m')}"
    st.caption(caption)


def render_material_section(target: str, label: str, raw_df, narratives, risk_df):
    st.header(label)
    signal_df = load_signal_table(target)

    col_chart, col_side = st.columns([2, 1])

    with col_chart:
        if signal_df is None:
            st.warning(
                f"output/procurement_signal_{target}.csv not found - run procurement_signal.py first."
            )
        else:
            fig = plot_forecast_chart(raw_df, signal_df, target, label)
            st.pyplot(fig)

    with col_side:
        st.subheader("Procurement signal")
        if signal_df is None:
            st.info("No signal table available.")
        else:
            display_cols = ["month", "forecasted_price", "confidence", "recommendation"]
            st.dataframe(signal_df[display_cols], hide_index=True, use_container_width=True)

    st.subheader("Forecast narrative")
    if signal_df is not None and not signal_df.empty:
        next_month = signal_df["month"].iloc[0]
        narrative = find_narrative(narratives, label, next_month)
        if narrative:
            st.info(narrative)
        else:
            st.info("output/forecast_narratives.txt not found or has no entry for this month - "
                    "run narrative_generator.py first.")
    else:
        st.info("No narrative available without a signal table.")

    if risk_df is not None and raw_df is not None and not risk_df.empty:
        latest_actual_month = raw_df.index.max().strftime("%Y-%m")
        active = risk_df[
            (risk_df["month"] == latest_actual_month)
            & risk_df["affected_targets"].str.contains(target, na=False)
        ]
        if not active.empty:
            lines = [
                f"{row.driver} moved {row.pct_change:+.0f}% (z={row.z_score:+.2f})"
                for row in active.itertuples()
            ]
            st.warning(f"Active risk alert for {latest_actual_month}: " + "; ".join(lines))

    st.divider()


def render_knowledge_graph():
    with st.expander("Causal knowledge graph (drivers -> price)"):
        html = load_graph_html()
        if html is None:
            st.info("output/price_driver_graph.html not found - run main.py first.")
        else:
            components.html(html, height=800, scrolling=True)


def main():
    try:
        raw_df = load_raw_prices()
        narratives = load_narratives()
        risk_df = load_risk_alerts()

        render_header(raw_df)

        if raw_df is None:
            st.warning("data/rm_price_data.csv not found - run fetch_data.py first. "
                       "Charts will skip recent-history context but forecasts may still show.")

        for target, label in MATERIALS.items():
            render_material_section(target, label, raw_df, narratives, risk_df)

        render_knowledge_graph()

    except Exception as e:
        st.error(f"Dashboard hit an unexpected error and could not render fully: {e}")


if __name__ == "__main__":
    main()
