# Raw Material Price Forecasting - Aluminium & PVC Resin

## Dashboard

A minimal Streamlit dashboard reads the saved outputs (no live API calls,
no live model refitting) and displays forecasts, procurement signals, the
auto-generated narrative, any active risk alerts, and the causal knowledge
graph.

Run it with:

```bash
streamlit run src/dashboard.py
```

Run the pipeline first (in order) so the dashboard has fresh files to read:

```bash
python src/fetch_data.py
python src/correlation_analysis.py
python src/feature_engineering.py
python src/forecast_model.py
python src/procurement_signal.py
python src/risk_alerts.py
python src/narrative_generator.py
python main.py
```
