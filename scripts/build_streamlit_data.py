"""Build a compact app-ready data package for Streamlit Cloud deployment."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
TABLES_DIR = OUTPUTS_DIR / "tables"
FORECAST_DIR = OUTPUTS_DIR / "forecasts"
INSIGHTS_DIR = OUTPUTS_DIR / "insights"
APP_DATA_DIR = PROJECT_ROOT / "streamlit_app" / "data"

BOOKING_APP_COLUMNS = [
    "booking_id",
    "hotel",
    "is_canceled",
    "lead_time",
    "arrival_date_month",
    "arrival_date",
    "arrival_year_month",
    "country",
    "market_segment",
    "distribution_channel",
    "is_repeated_guest",
    "previous_cancellations",
    "deposit_type",
    "customer_type",
    "total_guests",
    "total_nights",
    "total_of_special_requests",
    "adr_clean",
    "lead_time_band",
    "realized_room_nights",
    "realized_revenue",
    "lost_revenue_estimate",
    "booking_reliability_score",
    "cancellation_risk_tier",
]

COPY_SPECS = [
    (PROCESSED_DIR / "monthly_demand.csv", "monthly_demand.csv"),
    (PROCESSED_DIR / "customer_segment_performance.csv", "customer_segment_performance.csv"),
    (PROCESSED_DIR / "forecasting_input_monthly.csv", "forecasting_input_monthly.csv"),
    (TABLES_DIR / "booking_source_scorecard.csv", "booking_source_scorecard.csv"),
    (TABLES_DIR / "cancellation_risk_matrix.csv", "cancellation_risk_matrix.csv"),
    (TABLES_DIR / "customer_persona_segments.csv", "customer_persona_segments.csv"),
    (TABLES_DIR / "revenue_optimization_plan.csv", "revenue_optimization_plan.csv"),
    (TABLES_DIR / "seasonal_occupancy_scorecard.csv", "seasonal_occupancy_scorecard.csv"),
    (FORECAST_DIR / "booking_demand_forecast.csv", "booking_demand_forecast.csv"),
    (FORECAST_DIR / "occupancy_rate_forecast.csv", "occupancy_rate_forecast.csv"),
    (FORECAST_DIR / "revenue_forecast.csv", "revenue_forecast.csv"),
    (FORECAST_DIR / "forecast_accuracy_metrics.json", "forecast_accuracy_metrics.json"),
    (INSIGHTS_DIR / "kpi_summary.json", "kpi_summary.json"),
]


def require_file(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return path


def file_size_mb(path: Path) -> float:
    return path.stat().st_size / 1024 / 1024


def build_bookings_app_table() -> Path:
    source_path = require_file(PROCESSED_DIR / "hotel_bookings_cleaned.csv")
    bookings = pd.read_csv(source_path, usecols=BOOKING_APP_COLUMNS, parse_dates=["arrival_date"])
    bookings = bookings.sort_values(["arrival_date", "hotel", "booking_id"])

    output_path = APP_DATA_DIR / "bookings_app.csv.gz"
    bookings.to_csv(output_path, index=False, compression="gzip")
    return output_path


def copy_supporting_outputs() -> list[Path]:
    copied_paths: list[Path] = []
    for source_path, target_name in COPY_SPECS:
        target_path = APP_DATA_DIR / target_name
        shutil.copy2(require_file(source_path), target_path)
        copied_paths.append(target_path)
    return copied_paths


def write_manifest(paths: list[Path]) -> None:
    manifest = {
        "purpose": "Compact Streamlit Cloud deployment data package",
        "source": "Generated from local processed analytics outputs",
        "files": [
            {
                "file": path.name,
                "size_mb": round(file_size_mb(path), 4),
            }
            for path in sorted(paths)
        ],
    }
    (APP_DATA_DIR / "app_data_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def run() -> None:
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    paths = [build_bookings_app_table(), *copy_supporting_outputs()]
    write_manifest(paths)
    total_size = sum(file_size_mb(path) for path in APP_DATA_DIR.glob("*") if path.is_file())
    print(f"Streamlit app data package created at {APP_DATA_DIR}")
    print(f"Total app data size: {total_size:.2f} MB")


if __name__ == "__main__":
    run()
