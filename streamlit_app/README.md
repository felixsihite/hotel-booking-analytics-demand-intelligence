# Streamlit Enterprise Analytics Application

This folder contains the recruiter-facing Streamlit application for Hotel Booking Analytics & Demand Intelligence.

Run locally:

```bash
streamlit run streamlit_app/app.py
```

Streamlit Cloud main file path:

```text
streamlit_app/app.py
```

The app uses generated analytical outputs from:

- `data/processed/`
- `outputs/tables/`
- `outputs/forecasts/`
- `outputs/insights/`

Run `python scripts/run_pipeline.py` first if these files need to be regenerated locally. Install `requirements-dev.txt` before regenerating the full pipeline.

The app is the primary portfolio interface for this project. No separate static web front end or external dashboard tool is required.
