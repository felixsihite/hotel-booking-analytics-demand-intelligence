"""Enterprise data preparation for Hotel Booking Analytics.

This script converts the Kaggle Hotel Booking Demand dataset into a set of
SQL-ready analytical tables, KPI extracts, forecasting inputs, and a local
SQLite warehouse.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "hotel_bookings.csv"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
WAREHOUSE_DIR = PROJECT_ROOT / "data" / "warehouse"
OUTPUT_TABLES_DIR = PROJECT_ROOT / "outputs" / "tables"
OUTPUT_INSIGHTS_DIR = PROJECT_ROOT / "outputs" / "insights"

MONTH_ORDER = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

SEASON_MAP = {
    "December": "Winter",
    "January": "Winter",
    "February": "Winter",
    "March": "Spring",
    "April": "Spring",
    "May": "Spring",
    "June": "Summer",
    "July": "Summer",
    "August": "Summer",
    "September": "Autumn",
    "October": "Autumn",
    "November": "Autumn",
}

LEAD_TIME_LABELS = [
    "Same week",
    "1-4 weeks",
    "1-3 months",
    "3-6 months",
    "6-12 months",
    "12+ months",
]


def ensure_directories() -> None:
    """Create output directories used by the pipeline."""
    for path in [PROCESSED_DIR, WAREHOUSE_DIR, OUTPUT_TABLES_DIR, OUTPUT_INSIGHTS_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def load_raw_data(path: Path = RAW_PATH) -> pd.DataFrame:
    """Load the raw dataset and validate the expected business-critical fields."""
    if not path.exists():
        raise FileNotFoundError(f"Raw dataset not found at {path}")

    df = pd.read_csv(path)
    required_columns = {
        "hotel",
        "is_canceled",
        "lead_time",
        "arrival_date_year",
        "arrival_date_month",
        "arrival_date_day_of_month",
        "adr",
        "reservation_status_date",
    }
    missing = required_columns.difference(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {sorted(missing)}")
    return df


def standardize_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize categorical values without changing the core business meaning."""
    cleaned = df.copy()
    categorical_columns = cleaned.select_dtypes(include=["object"]).columns
    for column in categorical_columns:
        cleaned[column] = cleaned[column].astype("string").str.strip()

    unknown_fill = {
        "country": "Unknown",
        "meal": "Undefined",
        "market_segment": "Undefined",
        "distribution_channel": "Undefined",
        "customer_type": "Undefined",
        "deposit_type": "Undefined",
        "reserved_room_type": "Unknown",
        "assigned_room_type": "Unknown",
        "reservation_status": "Unknown",
    }
    for column, value in unknown_fill.items():
        if column in cleaned:
            cleaned[column] = cleaned[column].fillna(value).replace({"": value, "nan": value})

    cleaned["country"] = cleaned["country"].str.upper()
    cleaned["hotel"] = cleaned["hotel"].replace(
        {"City Hotel": "City Hotel", "Resort Hotel": "Resort Hotel"}
    )
    return cleaned


def add_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Create robust arrival and reservation dates."""
    enriched = df.copy()
    enriched["arrival_month_number"] = (
        pd.Categorical(enriched["arrival_date_month"], categories=MONTH_ORDER, ordered=True)
        .codes.astype("int64")
        + 1
    )
    enriched["arrival_date"] = pd.to_datetime(
        {
            "year": enriched["arrival_date_year"],
            "month": enriched["arrival_month_number"],
            "day": enriched["arrival_date_day_of_month"],
        },
        errors="coerce",
    )
    enriched["reservation_status_date"] = pd.to_datetime(
        enriched["reservation_status_date"], errors="coerce"
    )
    enriched["arrival_year_month"] = enriched["arrival_date"].dt.to_period("M").astype(str)
    enriched["arrival_quarter"] = enriched["arrival_date"].dt.to_period("Q").astype(str)
    enriched["arrival_day_name"] = enriched["arrival_date"].dt.day_name()
    enriched["season"] = enriched["arrival_date_month"].map(SEASON_MAP).fillna("Unknown")
    return enriched


def add_booking_features(df: pd.DataFrame) -> pd.DataFrame:
    """Engineer booking, occupancy, cancellation, and revenue intelligence fields."""
    enriched = df.copy()

    enriched["children"] = enriched["children"].fillna(0).astype(int)
    enriched["agent"] = enriched["agent"].fillna(0).astype(int)
    enriched["company"] = enriched["company"].fillna(0).astype(int)

    enriched["has_agent"] = (enriched["agent"] > 0).astype(int)
    enriched["has_company"] = (enriched["company"] > 0).astype(int)
    enriched["total_guests"] = enriched["adults"] + enriched["children"] + enriched["babies"]
    enriched["total_nights"] = (
        enriched["stays_in_weekend_nights"] + enriched["stays_in_week_nights"]
    )
    enriched["weekend_share"] = np.where(
        enriched["total_nights"] > 0,
        enriched["stays_in_weekend_nights"] / enriched["total_nights"],
        0,
    )
    enriched["is_family_booking"] = (
        (enriched["children"] + enriched["babies"]) > 0
    ).astype(int)
    enriched["room_type_changed"] = (
        enriched["reserved_room_type"] != enriched["assigned_room_type"]
    ).astype(int)
    enriched["is_transient"] = (enriched["customer_type"] == "Transient").astype(int)
    enriched["is_group_or_contract"] = enriched["customer_type"].isin(
        ["Contract", "Group", "Transient-Party"]
    ).astype(int)

    enriched["zero_guest_flag"] = (enriched["total_guests"] <= 0).astype(int)
    enriched["zero_night_flag"] = (enriched["total_nights"] <= 0).astype(int)
    enriched["negative_adr_flag"] = (enriched["adr"] < 0).astype(int)
    enriched["extreme_lead_time_flag"] = (enriched["lead_time"] > 365).astype(int)

    adr_working = enriched["adr"].where(enriched["adr"] >= 0)
    adr_cap = adr_working.quantile(0.995)
    adr_floor = adr_working.quantile(0.005)
    enriched["adr_outlier_flag"] = (
        (enriched["adr"] < 0) | (enriched["adr"] > adr_cap)
    ).astype(int)
    enriched["adr_clean"] = adr_working.clip(lower=adr_floor, upper=adr_cap)
    enriched["adr_clean"] = enriched["adr_clean"].fillna(enriched["adr_clean"].median())

    enriched["lead_time_band"] = pd.cut(
        enriched["lead_time"],
        bins=[-1, 7, 30, 90, 180, 365, np.inf],
        labels=LEAD_TIME_LABELS,
    ).astype(str)
    enriched["stay_length_band"] = pd.cut(
        enriched["total_nights"],
        bins=[-1, 0, 2, 4, 7, 14, np.inf],
        labels=["0 nights", "1-2 nights", "3-4 nights", "5-7 nights", "8-14 nights", "15+ nights"],
    ).astype(str)
    enriched["guest_size_segment"] = pd.cut(
        enriched["total_guests"],
        bins=[-1, 0, 1, 2, 4, np.inf],
        labels=["Invalid", "Solo", "Couple", "Small group", "Large group"],
    ).astype(str)

    enriched["gross_booking_value"] = enriched["adr_clean"] * enriched["total_nights"]
    enriched["realized_room_nights"] = np.where(
        enriched["is_canceled"] == 0, enriched["total_nights"], 0
    )
    enriched["canceled_room_nights"] = np.where(
        enriched["is_canceled"] == 1, enriched["total_nights"], 0
    )
    enriched["realized_revenue"] = np.where(
        enriched["is_canceled"] == 0, enriched["gross_booking_value"], 0
    )
    enriched["lost_revenue_estimate"] = np.where(
        enriched["is_canceled"] == 1, enriched["gross_booking_value"], 0
    )
    enriched["booking_reliability_score"] = (
        100
        - enriched["is_canceled"] * 40
        - np.minimum(enriched["previous_cancellations"], 3) * 10
        - enriched["extreme_lead_time_flag"] * 10
        + np.minimum(enriched["total_of_special_requests"], 3) * 5
        + enriched["is_repeated_guest"] * 10
    ).clip(0, 100)
    enriched["cancellation_risk_tier"] = pd.cut(
        100 - enriched["booking_reliability_score"],
        bins=[-1, 20, 45, 70, 101],
        labels=["Low", "Moderate", "High", "Critical"],
    ).astype(str)

    return enriched


def clean_bookings(df: pd.DataFrame) -> pd.DataFrame:
    """Run the complete cleaning and feature engineering workflow."""
    cleaned = (
        df.pipe(standardize_categoricals)
        .pipe(add_dates)
        .pipe(add_booking_features)
        .copy()
    )

    cleaned = cleaned[cleaned["zero_guest_flag"] == 0].copy()
    cleaned = cleaned.sort_values(["arrival_date", "hotel", "reservation_status_date"])
    cleaned.insert(0, "booking_id", np.arange(1, len(cleaned) + 1))
    return cleaned


def create_monthly_demand_table(bookings: pd.DataFrame) -> pd.DataFrame:
    """Create hotel-month demand, occupancy, revenue, and cancellation KPIs."""
    monthly = (
        bookings.groupby(["hotel", "arrival_year_month"], observed=False)
        .agg(
            arrival_date=("arrival_date", "min"),
            bookings=("booking_id", "count"),
            cancellations=("is_canceled", "sum"),
            room_nights_requested=("total_nights", "sum"),
            room_nights_realized=("realized_room_nights", "sum"),
            room_nights_canceled=("canceled_room_nights", "sum"),
            gross_booking_value=("gross_booking_value", "sum"),
            realized_revenue=("realized_revenue", "sum"),
            lost_revenue_estimate=("lost_revenue_estimate", "sum"),
            adr=("adr_clean", "mean"),
            average_lead_time=("lead_time", "mean"),
            total_guests=("total_guests", "sum"),
            repeat_guest_rate=("is_repeated_guest", "mean"),
            special_request_rate=("total_of_special_requests", "mean"),
        )
        .reset_index()
    )
    monthly["cancellation_rate"] = monthly["cancellations"] / monthly["bookings"]

    capacity_proxy = (
        monthly.groupby("hotel")["room_nights_realized"].transform("max").replace(0, np.nan)
        * 1.08
    )
    monthly["capacity_room_night_proxy"] = capacity_proxy.round(2)
    monthly["occupancy_rate_estimate"] = (
        monthly["room_nights_realized"] / monthly["capacity_room_night_proxy"]
    ).clip(0, 1)
    monthly["revenue_opportunity_index"] = (
        (1 - monthly["occupancy_rate_estimate"]).fillna(0) * 0.55
        + monthly["cancellation_rate"].fillna(0) * 0.30
        + (
            monthly["lost_revenue_estimate"]
            / monthly["gross_booking_value"].replace(0, np.nan)
        ).fillna(0)
        * 0.15
    ).clip(0, 1)
    monthly["revpar_estimate"] = (
        monthly["realized_revenue"] / monthly["capacity_room_night_proxy"].replace(0, np.nan)
    ).fillna(0)
    monthly["year"] = pd.to_datetime(monthly["arrival_date"]).dt.year
    monthly["month"] = pd.to_datetime(monthly["arrival_date"]).dt.month
    monthly["month_name"] = pd.to_datetime(monthly["arrival_date"]).dt.month_name()
    return monthly.sort_values(["hotel", "arrival_date"])


def create_segment_table(bookings: pd.DataFrame) -> pd.DataFrame:
    """Aggregate customer and channel segments for business intelligence."""
    segment_columns = [
        "hotel",
        "market_segment",
        "distribution_channel",
        "customer_type",
        "lead_time_band",
        "deposit_type",
    ]
    segments = (
        bookings.groupby(segment_columns, observed=False)
        .agg(
            bookings=("booking_id", "count"),
            cancellations=("is_canceled", "sum"),
            realized_revenue=("realized_revenue", "sum"),
            lost_revenue_estimate=("lost_revenue_estimate", "sum"),
            room_nights_realized=("realized_room_nights", "sum"),
            adr=("adr_clean", "mean"),
            average_lead_time=("lead_time", "mean"),
            repeat_guest_rate=("is_repeated_guest", "mean"),
            average_special_requests=("total_of_special_requests", "mean"),
        )
        .reset_index()
    )
    segments["cancellation_rate"] = segments["cancellations"] / segments["bookings"]
    segments["revenue_per_booking"] = segments["realized_revenue"] / segments["bookings"]
    segments["segment_risk_score"] = (
        segments["cancellation_rate"] * 60
        + (segments["average_lead_time"] / segments["average_lead_time"].max()).fillna(0) * 20
        + (
            segments["lost_revenue_estimate"]
            / segments["lost_revenue_estimate"].max()
        ).fillna(0)
        * 20
    ).round(2)
    return segments.sort_values(["segment_risk_score", "bookings"], ascending=[False, False])


def create_forecasting_inputs(monthly: pd.DataFrame) -> pd.DataFrame:
    """Create a compact time-series table suitable for R and Python forecasting."""
    ts = (
        monthly.groupby("arrival_date")
        .agg(
            bookings=("bookings", "sum"),
            cancellations=("cancellations", "sum"),
            room_nights_requested=("room_nights_requested", "sum"),
            room_nights_realized=("room_nights_realized", "sum"),
            gross_booking_value=("gross_booking_value", "sum"),
            realized_revenue=("realized_revenue", "sum"),
            lost_revenue_estimate=("lost_revenue_estimate", "sum"),
            capacity_room_night_proxy=("capacity_room_night_proxy", "sum"),
        )
        .reset_index()
        .rename(columns={"arrival_date": "ds"})
    )
    ts["cancellation_rate"] = ts["cancellations"] / ts["bookings"]
    ts["occupancy_rate_estimate"] = (
        ts["room_nights_realized"] / ts["capacity_room_night_proxy"].replace(0, np.nan)
    ).clip(0, 1)
    ts["average_daily_rate_proxy"] = ts["realized_revenue"] / ts[
        "room_nights_realized"
    ].replace(0, np.nan)
    ts["y_booking_demand"] = ts["bookings"]
    ts["y_occupancy_rate"] = ts["occupancy_rate_estimate"]
    ts["y_revenue"] = ts["realized_revenue"]
    return ts.sort_values("ds")


def create_kpi_summary(bookings: pd.DataFrame, monthly: pd.DataFrame) -> dict[str, float | int]:
    """Calculate executive KPI metrics used by reports and dashboards."""
    total_bookings = int(bookings["booking_id"].nunique())
    cancellation_rate = float(bookings["is_canceled"].mean())
    realized_revenue = float(bookings["realized_revenue"].sum())
    lost_revenue = float(bookings["lost_revenue_estimate"].sum())
    total_room_nights = float(bookings["realized_room_nights"].sum())
    occupancy_rate = float(
        monthly["room_nights_realized"].sum()
        / monthly["capacity_room_night_proxy"].sum()
    )
    roi = float(monthly["revenue_opportunity_index"].mean())
    revpar = float(
        monthly["realized_revenue"].sum()
        / monthly["capacity_room_night_proxy"].sum()
    )

    return {
        "total_bookings": total_bookings,
        "date_min": str(bookings["arrival_date"].min().date()),
        "date_max": str(bookings["arrival_date"].max().date()),
        "cancellation_rate": round(cancellation_rate, 4),
        "estimated_occupancy_rate": round(occupancy_rate, 4),
        "realized_revenue": round(realized_revenue, 2),
        "lost_revenue_estimate": round(lost_revenue, 2),
        "room_nights_realized": round(total_room_nights, 2),
        "average_daily_rate": round(float(bookings["adr_clean"].mean()), 2),
        "revpar_estimate": round(revpar, 2),
        "average_lead_time": round(float(bookings["lead_time"].mean()), 2),
        "repeat_guest_rate": round(float(bookings["is_repeated_guest"].mean()), 4),
        "revenue_opportunity_index": round(roi, 4),
    }


def export_tables(
    bookings: pd.DataFrame,
    monthly: pd.DataFrame,
    segments: pd.DataFrame,
    forecasting: pd.DataFrame,
    kpis: dict[str, float | int],
) -> None:
    """Persist CSV, Parquet, JSON, and SQLite assets."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)

    bookings.to_csv(PROCESSED_DIR / "hotel_bookings_cleaned.csv", index=False)
    monthly.to_csv(PROCESSED_DIR / "monthly_demand.csv", index=False)
    segments.to_csv(PROCESSED_DIR / "customer_segment_performance.csv", index=False)
    forecasting.to_csv(PROCESSED_DIR / "forecasting_input_monthly.csv", index=False)
    pd.DataFrame([kpis]).to_csv(OUTPUT_TABLES_DIR / "executive_kpis.csv", index=False)

    try:
        bookings.to_parquet(PROCESSED_DIR / "hotel_bookings_cleaned.parquet", index=False)
        monthly.to_parquet(PROCESSED_DIR / "monthly_demand.parquet", index=False)
        forecasting.to_parquet(PROCESSED_DIR / "forecasting_input_monthly.parquet", index=False)
    except Exception as exc:  # pragma: no cover - optional dependency resilience
        print(f"Parquet export skipped: {exc}")

    with (OUTPUT_INSIGHTS_DIR / "kpi_summary.json").open("w", encoding="utf-8") as fp:
        json.dump(kpis, fp, indent=2)

    db_path = WAREHOUSE_DIR / "hotel_booking_analytics.sqlite"
    with sqlite3.connect(db_path) as conn:
        bookings.to_sql("fact_bookings", conn, if_exists="replace", index=False)
        monthly.to_sql("mart_monthly_demand", conn, if_exists="replace", index=False)
        segments.to_sql("mart_customer_segments", conn, if_exists="replace", index=False)
        forecasting.to_sql("mart_forecasting_monthly", conn, if_exists="replace", index=False)
        pd.DataFrame([kpis]).to_sql("mart_executive_kpis", conn, if_exists="replace", index=False)


def run() -> dict[str, float | int]:
    """Execute the full data preparation workflow."""
    ensure_directories()
    raw = load_raw_data()
    bookings = clean_bookings(raw)
    monthly = create_monthly_demand_table(bookings)
    segments = create_segment_table(bookings)
    forecasting = create_forecasting_inputs(monthly)
    kpis = create_kpi_summary(bookings, monthly)
    export_tables(bookings, monthly, segments, forecasting, kpis)

    print("Data cleaning and feature engineering complete.")
    print(f"Cleaned bookings: {len(bookings):,}")
    print(f"Processed data written to: {PROCESSED_DIR}")
    print(f"SQLite warehouse written to: {WAREHOUSE_DIR / 'hotel_booking_analytics.sqlite'}")
    return kpis


if __name__ == "__main__":
    run()