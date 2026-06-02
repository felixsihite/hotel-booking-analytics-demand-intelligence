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

The app uses a compact deployment data package from:

- `streamlit_app/data/`

Refresh the compact package with:

```bash
python scripts/build_streamlit_data.py
```

Run `python scripts/run_pipeline.py` first if the full local analytics outputs need to be regenerated. Install `requirements-dev.txt` before regenerating the full pipeline.

The app is the primary portfolio interface for this project. No separate static web front end or external dashboard tool is required.
