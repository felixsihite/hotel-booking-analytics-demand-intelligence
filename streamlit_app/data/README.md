# Streamlit App Data

This folder contains the compact app-ready data package used by Streamlit Cloud.

Generate or refresh it locally with:

```bash
python scripts/build_streamlit_data.py
```

The package is intentionally much smaller than the full raw, processed, and warehouse files so the deployed app starts faster while preserving the recruiter-facing analytics experience.
