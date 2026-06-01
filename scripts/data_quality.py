"""Generate data quality and data dictionary documentation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "hotel_bookings.csv"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_REPORTS_DIR = PROJECT_ROOT / "outputs" / "reports"
OUTPUT_TABLES_DIR = PROJECT_ROOT / "outputs" / "tables"
DOCS_DIR = PROJECT_ROOT / "docs"


BUSINESS_DEFINITIONS = {
    "booking_id": "Unique analytical booking identifier generated during preprocessing.",
    "hotel": "Hotel type: City Hotel or Resort Hotel.",
    "is_canceled": "Cancellation flag where 1 means canceled and 0 means not canceled.",
    "lead_time": "Number of days between booking creation and arrival date.",
    "arrival_date": "Constructed guest arrival date.",
    "arrival_year_month": "Arrival period in YYYY-MM format.",
    "season": "Arrival season derived from arrival month.",
    "market_segment": "Commercial market segment for the reservation.",
    "distribution_channel": "Booking distribution channel.",
    "customer_type": "Customer contract or booking type.",
    "total_guests": "Total adults, children, and babies.",
    "total_nights": "Weekend nights plus week nights.",
    "lead_time_band": "Business-friendly lead-time category.",
    "guest_size_segment": "Guest-size category for customer behavior analysis.",
    "adr_clean": "Cleaned average daily rate after negative values and extreme outliers are handled.",
    "gross_booking_value": "Estimated booking value using cleaned ADR multiplied by total nights.",
    "realized_revenue": "Estimated revenue retained from non-canceled bookings.",
    "lost_revenue_estimate": "Estimated revenue exposure from canceled bookings.",
    "realized_room_nights": "Room nights retained from non-canceled bookings.",
    "canceled_room_nights": "Room nights lost to canceled bookings.",
    "booking_reliability_score": "Composite reliability score based on cancellation, lead time, prior cancellation, repeat guest, and special request signals.",
    "cancellation_risk_tier": "Low, Moderate, High, or Critical cancellation risk grouping.",
    "occupancy_rate_estimate": "Estimated occupancy using realized room nights divided by capacity proxy.",
    "revpar_estimate": "Estimated revenue per available room using realized revenue divided by capacity proxy.",
    "revenue_opportunity_index": "Composite opportunity metric combining occupancy gap, cancellation rate, and lost revenue share.",
}


def pct(value: float) -> str:
    return f"{value:.2%}"


def write_data_dictionary(bookings: pd.DataFrame, monthly: pd.DataFrame) -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    combined = {
        "hotel_bookings_cleaned": bookings,
        "monthly_demand": monthly,
    }
    for table_name, frame in combined.items():
        for column in frame.columns:
            rows.append(
                {
                    "table": table_name,
                    "column": column,
                    "dtype": str(frame[column].dtype),
                    "non_null_rate": round(float(frame[column].notna().mean()), 4),
                    "business_definition": BUSINESS_DEFINITIONS.get(column, "Source or engineered analytical field."),
                }
            )
    dictionary = pd.DataFrame(rows)
    dictionary.to_csv(OUTPUT_TABLES_DIR / "data_dictionary.csv", index=False)

    lines = [
        "# Data Dictionary",
        "",
        "This document describes the primary analytical tables used by the Streamlit application and SQL BI layer.",
        "",
    ]
    for table_name, group in dictionary.groupby("table"):
        lines.extend([f"## {table_name}", "", "| Column | Type | Non-Null Rate | Business Definition |", "|---|---:|---:|---|"])
        for row in group.itertuples():
            lines.append(
                f"| {row.column} | {row.dtype} | {pct(row.non_null_rate)} | {row.business_definition} |"
            )
        lines.append("")
    (DOCS_DIR / "data_dictionary.md").write_text("\n".join(lines), encoding="utf-8")


def run() -> None:
    OUTPUT_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_TABLES_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    raw = pd.read_csv(RAW_PATH)
    bookings = pd.read_csv(PROCESSED_DIR / "hotel_bookings_cleaned.csv", parse_dates=["arrival_date"])
    monthly = pd.read_csv(PROCESSED_DIR / "monthly_demand.csv", parse_dates=["arrival_date"])
    forecasting = pd.read_csv(PROCESSED_DIR / "forecasting_input_monthly.csv", parse_dates=["ds"])

    quality_checks = [
        ("Raw rows", len(raw), "Reference input volume"),
        ("Processed booking rows", len(bookings), "Cleaned analytical booking rows"),
        ("Removed invalid rows", len(raw) - len(bookings), "Rows removed during preprocessing, primarily invalid guest records"),
        ("Processed duplicate booking_id", int(bookings["booking_id"].duplicated().sum()), "Should be 0"),
        ("Missing arrival_date", int(bookings["arrival_date"].isna().sum()), "Should be 0"),
        ("Zero guest records", int((bookings["total_guests"] <= 0).sum()), "Should be 0 after cleaning"),
        ("Negative ADR after cleaning", int((bookings["adr_clean"] < 0).sum()), "Should be 0"),
        ("ADR outlier flags retained", int(bookings["adr_outlier_flag"].sum()), "Flags retained for auditability"),
        ("Monthly demand rows", len(monthly), "Hotel-month analytical mart"),
        ("Forecast input rows", len(forecasting), "Monthly time-series rows"),
    ]
    summary = pd.DataFrame(quality_checks, columns=["check", "value", "interpretation"])
    summary.to_csv(OUTPUT_TABLES_DIR / "data_quality_summary.csv", index=False)

    raw_missing = (
        raw.isna()
        .mean()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"index": "column", 0: "missing_rate"})
    )
    raw_missing.to_csv(OUTPUT_TABLES_DIR / "raw_missing_value_profile.csv", index=False)

    write_data_dictionary(bookings, monthly)

    top_missing = "\n".join(
        f"- {row.column}: {pct(row.missing_rate)}"
        for row in raw_missing.head(8).itertuples()
    )
    report = f"""# Data Quality Report

## Summary

The dataset has been cleaned and converted into SQL-ready analytical tables for hospitality analytics, forecasting, segmentation, cancellation risk, and revenue optimization.

## Core Data Health Checks

| Check | Value | Interpretation |
|---|---:|---|
"""
    for row in summary.itertuples():
        report += f"| {row.check} | {row.value:,} | {row.interpretation} |\n"

    report += f"""
## Raw Missing Value Profile

Top raw missing-value fields:

{top_missing}

## Cleaning Decisions

- Missing `company` and `agent` identifiers are converted to `0` and paired with binary indicators for auditability.
- Missing `country` values are assigned to `Unknown`.
- Missing `children` values are imputed to `0`.
- Negative ADR values and extreme ADR values are handled through the engineered `adr_clean` field.
- Invalid zero-guest bookings are removed from the cleaned analytical dataset.
- Outlier and anomaly flags are retained so the cleaning process stays transparent.

## Professional Use Notes

The dataset does not include true room inventory. Occupancy and RevPAR are therefore estimated using a capacity proxy derived from observed realized room-night peaks by hotel. This is clearly documented for portfolio transparency and should be replaced with actual inventory data in production.
"""
    (OUTPUT_REPORTS_DIR / "data_quality_report.md").write_text(report, encoding="utf-8")
    print("Data quality report and data dictionary generated.")


if __name__ == "__main__":
    run()