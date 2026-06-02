"""Run the complete Python analytics pipeline."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import booking_analysis
import build_streamlit_data
import cancellation_analysis
import customer_segmentation
import data_cleaning
import data_quality
import generate_business_reports
import occupancy_analysis
import visualization


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_script(script_name: str) -> None:
    script_path = PROJECT_ROOT / "scripts" / script_name
    subprocess.run([sys.executable, str(script_path)], cwd=PROJECT_ROOT, check=True)


def main() -> None:
    data_cleaning.run()
    data_quality.run()
    booking_analysis.run()
    cancellation_analysis.run()
    occupancy_analysis.run()
    customer_segmentation.run()
    visualization.create_all_charts()
    run_script("demand_forecasting.py")
    generate_business_reports.run()
    build_streamlit_data.run()
    run_script("generate_notebooks.py")
    print("Full hospitality analytics pipeline completed. Launch the dashboard with: streamlit run streamlit_app/app.py")


if __name__ == "__main__":
    main()
