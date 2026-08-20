# Raw Material Price Forecasting - Aluminium & PVC Resin

## React frontend (primary demo UI)

A static Vite + React + Tailwind app in `/frontend` - no backend server, reads
only from `frontend/public/data.json`, so it has zero risk of a live API call
failing on camera. Shows the 6-month forecast charts with prediction
intervals (recharts), procurement signal tables, auto-generated narratives, a
force-directed causal knowledge graph (d3-force, real correlation values on
hover), a live client-side what-if scenario panel, and the risk-alert
validation example.

```bash
python src/export_dashboard_data.py   # regenerate frontend/public/data.json
cd frontend
npm install                            # first time only
npm run dev                            # or: npm run build && npm run preview
```

Run the pipeline first (in order) so there's fresh data to export:

```bash
python src/fetch_data.py
python src/correlation_analysis.py
python src/feature_engineering.py
python src/forecast_model.py
python src/procurement_signal.py
python src/risk_alerts.py
python src/narrative_generator.py
python main.py
python src/export_dashboard_data.py
```

## Streamlit dashboard (legacy)

A minimal Streamlit dashboard reads the same saved outputs and displays the
same core information. Being replaced by the React frontend above, kept here
in case it's still useful.

```bash
streamlit run src/dashboard.py
```
